from fastapi import FastAPI

app = FastAPI(title="OlistIQ")

@app.get("/health")
def health():
    return {"status": "ok"}