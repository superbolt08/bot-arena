"""Run the built application at http://127.0.0.1:8000."""
import uvicorn

if __name__=="__main__":
    uvicorn.run("arena.server:app",host="127.0.0.1",port=8000)
