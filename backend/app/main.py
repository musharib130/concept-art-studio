from fastapi import FastAPI

app = FastAPI(title="Concept Art Studio API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
