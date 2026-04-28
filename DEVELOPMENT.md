# Development Guide

This document provides detailed instructions for setting up your development environment and contributing to the real-time-systems project.

## Prerequisites

- Python 3.10+
- pip or conda
- Git
- (Optional) Chrome/Chromium for PNG export functionality

## Local Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/theredplanetsings/real-time-systems.git
cd real-time-systems
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Running the Application

### Start the Dashboard

```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501` by default.

### Available Make Commands

```bash
make help      # Show all available commands
make test      # Run full test suite
make quick-test # Run core tests (faster)
make smoke     # Run Streamlit smoke tests
make fmt       # Auto-format code with black
make lint      # Check code quality with ruff
make fmt-check # Check formatting without changes
make check     # Run lint, fmt-check, and tests
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature-name
```

### 2. Make Changes

Follow the project's conventions:
- Keep changes focused on a single improvement
- Write or update tests for behavior changes
- Keep commit messages short and descriptive (1-4 words)

### 3. Test Locally

```bash
# During development
make quick-test

# Before committing
make check

# Test a specific page in Streamlit
streamlit run pages/00_Algorithm_Explorer.py
```

### 4. Format Code

```bash
make fmt
```

### 5. Commit and Push

```bash
git add .
git commit -m "brief descriptive message"
git push origin feature-name
```

### 6. Open a Pull Request

Submit a PR on GitHub with a clear description of changes.

## Project Structure

- **`pages/`**: Streamlit dashboard pages (the main UI)
- **`rt_utils.py`**: Core scheduling algorithms and plotting helpers
- **`scheduling_math.py`**: Mathematical helpers (utilization, density, hyperperiod, etc.)
- **`st_helpers.py`**: Streamlit UI components and shared controls
- **`tests/`**: Automated test suite
- **Algorithm folders** (`edf/`, `rm-dm-basics/`, etc.): Algorithm-specific code and reference schedules

## Writing Tests

Tests are located in `tests/` and use pytest:

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_schedulability_core.py

# Run tests with verbose output
pytest tests/ -v

# Run a specific test function
pytest tests/test_scheduling_math.py::test_utilisation
```

### Test Organization

- `test_schedulability_core.py`: Core algorithm logic
- `test_compare_metrics.py`: Compare mode calculations
- `test_scheduling_math.py`: Mathematical helpers
- `test_protocol_behaviors.py`: Resource protocols (PIP, PCP, NPP)
- `test_cyclic_executive.py`: Cyclic executive logic
- `test_streamlit_smoke.py`: Streamlit page existence and basic execution

### Test Markers

Tests are organized with pytest markers for easy filtering:

```bash
# Run only core algorithm tests
pytest -m core

# Run math and protocol tests
pytest -m "math or protocol"

# Skip slow tests
pytest -m "not slow"

# Run UI tests only
pytest -m ui
```

Available markers:
- `@pytest.mark.core`: Core scheduling algorithm tests
- `@pytest.mark.math`: Scheduling math and feasibility tests
- `@pytest.mark.protocol`: Resource protocol tests (PIP, PCP, NPP)
- `@pytest.mark.ui`: Streamlit page and UI tests
- `@pytest.mark.smoke`: Smoke tests for page existence
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.integration`: Integration tests across components

## Code Quality

The project uses:

- **Black**: Code formatting (100-char line length)
- **Ruff**: Linting (error and bug checks)
- **Type hints**: Throughout the codebase for better IDE support and error catching

### Check Code Quality

```bash
# Check formatting
make fmt-check

# Check for issues with ruff
make lint

# Auto-fix formatting
make fmt
```

## Debugging

### Streamlit Pages

For interactive debugging, use Streamlit's built-in debugging:

```bash
streamlit run pages/00_Algorithm_Explorer.py --logger.level=debug
```

### Python Debugger

For Python debugging, use `pdb`:

```python
import pdb; pdb.set_trace()  # Breakpoint
```

Or use your IDE's debugger.

### Testing Edge Cases

Run tests with more verbosity:

```bash
pytest tests/ -vv --tb=short
```

## Common Tasks

### Add a New Algorithm Page

1. Create a new file in `pages/` named `NN_Algorithm_Name.py`
2. Import shared utilities: `st_helpers`, `rt_utils`
3. Use the standard pattern for task input and visualization
4. Add tests in `tests/`

### Add a New Algorithm to the Registry

Edit `rt_utils.py` and add to the `ALGORITHM_FAMILIES` or `ALGORITHMS` dictionary.

### Add a New Test

Create a test file or add to an existing one in `tests/`:

```python
def test_new_feature():
    # Arrange
    tasks = [TaskSpec(1, 0, 10, 2, 10)]
    
    # Act
    result = your_function(tasks)
    
    # Assert
    assert result is not None
```

## Performance Profiling

For performance issues, use Python's `cProfile`:

```python
import cProfile
cProfile.run('your_function()')
```

## Documentation

- Update `README.md` for major changes
- Add docstrings to new functions
- Update `CHANGELOG.md` for significant improvements

## Troubleshooting

### Port Already in Use

If port 8501 is in use:

```bash
streamlit run streamlit_app.py --server.port 8502
```

### Import Errors

Ensure dependencies are installed:

```bash
pip install -r requirements-dev.txt
```

### Test Failures

Run a specific test with verbose output:

```bash
pytest tests/test_file.py::test_name -vv
```

## Resources

- [Real-time Systems Wikipedia](https://en.wikipedia.org/wiki/Real-time_computing)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [pytest Documentation](https://docs.pytest.org/)

## Questions?

Check existing issues or create a new one on GitHub.
