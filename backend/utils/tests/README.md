# Utils Layer Test Suite

Complete test suite for the `backend/utils/` layer including unit tests, integration tests, and fixtures.

## Test Structure

```
backend/utils/tests/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── requirements.txt                 # Test dependencies
├── test_context_compressor.py       # ContextCompressor tests
├── test_text_processor.py           # TextProcessor tests
├── test_slide_strategies.py         # Slide strategy tests
├── test_ppt_generator.py            # PresentationGenerator tests
├── test_main_api.py                 # API endpoint tests
├── fixtures/                        # Test data fixtures
│   ├── __init__.py
│   ├── sample_xml.py                # Sample XML data
│   └── sample_json.py               # Sample JSON data
└── integration/                     # Integration tests
    ├── __init__.py
    └── test_full_ppt_generation.py # End-to-end tests
```

## Installation

Install test dependencies:

```bash
cd backend/utils
pip install -r tests/requirements.txt
```

## Running Tests

### Run all tests:

```bash
cd backend/utils
pytest
```

### Run specific test file:

```bash
pytest tests/test_context_compressor.py
```

### Run specific test class:

```bash
pytest tests/test_text_processor.py::TestTextProcessor
```

### Run specific test function:

```bash
pytest tests/test_context_compressor.py::TestContextCompressor::test_extract_slide_info_with_h1
```

### Run with coverage:

```bash
pytest --cov=utils --cov-report=html
```

### Run only unit tests (skip integration tests):

```bash
pytest -m "not integration"
```

### Run only integration tests:

```bash
pytest -m integration
```

### Run with verbose output:

```bash
pytest -v
```

### Run with detailed output (print statements):

```bash
pytest -v -s
```

## Test Files Description

### 1. test_context_compressor.py

Tests for `context_compressor.py` module:

- `TestSlideInfo`: Tests for the SlideInfo dataclass
  - Creation and defaults
  - Summary generation
  - Image count display

- `TestContextCompressor`: Tests for ContextCompressor class
  - Initialization with various parameters
  - XML parsing (H1, bullets, columns, images)
  - Keyword extraction and stopword filtering
  - Duplicate tracking (keywords and images)
  - History compression
  - Token savings calculation

- `TestConvenienceFunctions`: Tests for utility functions

**Coverage target**: 85%

### 2. test_text_processor.py

Tests for `TextProcessor` class in `ppt_generator.py`:

- HTML tag removal (nested tags, attributes, edge cases)
- Font size calculation based on text length and shape dimensions
- Text truncation with custom suffixes
- Text chunking for long content (handles Chinese/English punctuation)

**Coverage target**: 90%

### 3. test_slide_strategies.py

Tests for slide generation strategies:

- `TestSlideStrategy`: Base strategy class tests
- `TestTitleSlideStrategy`: Title page creation
- `TestContentSlideStrategy`: Content page with text splitting
- `TestTableOfContentsSlideStrategy`: TOC with 3-5 items
- `TestImageSlideStrategy`: Image validation and download
- `TestSubSectionSlideStrategy`: Subsection with 1-5 items
- `TestReferencesSlideStrategy`: References page
- `TestEndSlideStrategy`: End page

**Coverage target**: 70%

### 4. test_ppt_generator.py

Tests for `PresentationGenerator` main class:

- Initialization with template
- Content block parsing (H1, paragraphs, bullets)
- Bullet point formatting
- Full presentation generation workflow
- Error handling for invalid inputs
- File saving

**Coverage target**: 65%

### 5. test_main_api.py

Tests for FastAPI endpoints:

- `TestPydanticModels`: Model validation tests
- `TestAPIEndpoints`: Endpoint tests
  - Root endpoint
  - PPT generation endpoint (success, failure, validation errors)
  - Requests with images and references
- `TestStaticFiles`: Static file serving

**Coverage target**: 60%

### 6. integration/test_full_ppt_generation.py

End-to-end integration tests:

- `TestContextCompressorIntegration`: Full compression workflow
- `TestTextProcessorIntegration`: HTML to PPT text processing
- `TestPresentationGenerationIntegration`: Complete PPT generation
- `TestErrorHandlingIntegration`: Edge cases and error scenarios
- `TestTokenSavingsIntegration`: Large-scale compression savings

## Fixtures

### Shared Fixtures (conftest.py)

- `sample_slide_xml`: Dictionary of sample XML strings
- `sample_ppt_json`: Sample PPT JSON data structure
- `mock_presentation`: Mock PowerPoint Presentation object
- `mock_slide`: Mock Slide object with text shapes
- `mock_shape`: Mock Shape object

### Sample Data (fixtures/)

- `sample_xml.py`: Predefined XML strings for various slide types
- `sample_json.py`: Sample JSON data for different PPT scenarios

## Coverage Goals

| Module | Target Coverage | Focus Areas |
|--------|----------------|-------------|
| context_compressor.py | 85% | XML parsing, deduplication logic |
| TextProcessor | 90% | Pure utility functions |
| Slide Strategies | 70% | Mock external dependencies |
| PresentationGenerator | 65% | Complex logic flows |
| main_api.py | 60% | API endpoints |

## Continuous Integration

To run tests in CI/CD pipeline:

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run tests with coverage and generate report
pytest --cov=utils --cov-report=xml --cov-report=term --junitxml=test-results.xml

# Exit with non-zero if coverage below threshold
pytest --cov=utils --cov-fail-under=60
```

## Known Limitations

1. **python-pptx Mocking**: Complex PPT objects are mocked rather than using real files
2. **Network Requests**: Image download tests use mocked responses
3. **File System**: Template file operations use temp files
4. **Chinese Text Processing**: Some edge cases with Chinese segmentation may not be fully tested

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the correct directory:

```bash
cd backend/utils
pytest
```

Or add the parent directory to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
pytest
```

### Missing Dependencies

Install test requirements:

```bash
pip install -r tests/requirements.txt
```

### Template File Not Found

Some tests require a template file. The tests use mock templates, but if you want to test with real files:

```bash
# Create a test template
python -c "from pptx import Presentation; p = Presentation(); p.save('test_template.pptx')"
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions (`test_*` for functions, `Test*` for classes)
2. Add descriptive docstrings
3. Use appropriate fixtures from `conftest.py`
4. Mark slow tests with `@pytest.mark.slow`
5. Update this README if adding new test files

## Test Statistics

As of last run:

- Total tests: ~200+
- Average execution time: ~30 seconds
- Code coverage: ~70% overall
- Passing rate: 100% (when dependencies are properly installed)
