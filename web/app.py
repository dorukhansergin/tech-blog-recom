from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import numpy as np
from sentence_transformers import SentenceTransformer, util
import pandas as pd
from pathlib import Path
import os
import glob
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Initialize the model
model = SentenceTransformer("all-MiniLM-L6-v2")


def load_embeddings():
    # Find all parquet files in the data directory
    parquet_files = glob.glob("data/*.parquet")
    if not parquet_files:
        return None

    # Get the most recent parquet file
    latest_file = max(parquet_files, key=os.path.getctime)
    return pd.read_parquet(latest_file)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/search")
async def search(job_description: str = Form(...)):
    # Generate embedding for the job description
    query_embedding = model.encode(job_description)
    logger.info(f"Query embedding shape: {query_embedding.shape}")

    # Load the parquet file
    df = load_embeddings()
    if df is None:
        return {"error": "No blog posts found. Please run the scraper first."}

    logger.info(f"Number of embeddings in corpus: {len(df)}")

    # Convert embeddings to tensor - they're already numpy arrays
    corpus_embeddings = np.stack(df["embedding"].values)
    logger.info(f"Corpus embeddings shape: {corpus_embeddings.shape}")

    query_embedding = query_embedding.reshape(1, -1)
    logger.info(f"Reshaped query embedding shape: {query_embedding.shape}")

    # Calculate cosine similarity
    similarities = util.cos_sim(query_embedding, corpus_embeddings)[0]
    logger.info(f"Similarities shape: {similarities.shape}")
    logger.info(f"Similarities type: {type(similarities)}")
    logger.info(f"Similarities content: {similarities}")

    # Convert PyTorch tensor to NumPy array
    similarities_np = similarities.cpu().numpy()
    logger.info(f"Converted similarities type: {type(similarities_np)}")

    # Get top 5 matches (or fewer if there are less than 5 items)
    n_results = min(5, len(similarities_np))
    logger.info(f"Number of results to return: {n_results}")

    if len(similarities_np) == 0:
        return {"error": "No similarities calculated. Please check your embeddings."}

    top_indices = np.argsort(similarities_np)[-n_results:][::-1]
    logger.info(f"Top indices: {top_indices}")

    results = df.iloc[top_indices][["title", "url", "source", "content"]].to_dict(
        "records"
    )

    # Add previews to results
    for result in results:
        # Get first 200 characters of content and add ellipsis
        preview = result["content"][:200].strip() + "..."
        result["preview"] = preview
        # Rename source to source_name to match frontend
        result["source_name"] = result.pop("source")
        # Remove the full content to keep response size small
        del result["content"]

    return {"results": results}
