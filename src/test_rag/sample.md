## Running the Test Pipeline

To verify that the Scrag pipeline works end-to-end, you can run a test command using the built-in CLI.

### Prerequisites

Before running the test, make sure you have all dependencies installed:

```bash
pip install -e .
pip install sentence-transformers
```

Inside src folder
```bash
python -m scrag.core.cli test-pipeline "https://en.wikipedia.org/wiki/Machine_learning"
```

You should be able to see the processed text, json and embeddings.