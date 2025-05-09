from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import numpy as np
from sentence_transformers import SentenceTransformer
import pandas as pd
from pathlib import Path
import os
import glob

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

    # Load the parquet file
    df = load_embeddings()
    if df is None:
        return {"error": "No blog posts found. Please run the scraper first."}

    # Calculate cosine similarity
    similarities = np.dot(df["embedding"].tolist(), query_embedding) / (
        np.linalg.norm(df["embedding"].tolist(), axis=1)
        * np.linalg.norm(query_embedding)
    )

    # Get top 5 matches
    top_indices = np.argsort(similarities)[-5:][::-1]
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
