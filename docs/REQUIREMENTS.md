# ClamAV GUI - Requirements & Installation

## System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.10 or higher (64-bit recommended)
- **Memory**: 512 MB RAM minimum, 1 GB recommended
- **Storage**: 100 MB free space for installation
- **Display**: 1024x768 minimum resolution

## Dependencies

### Core Runtime Dependencies

```txt
PySide6>=6.8.3          # Qt GUI framework
python-dotenv>=1.0.0    # Environment variable management
pywin32>=306            # Windows API bindings
wand>=0.6.10            # ImageMagick bindings for image processing
imagehash>=4.3.1        # Image hashing for duplicate detection
tqdm>=4.64.0            # Progress bars
qrcode>=7.4.2           # QR code generation
requests>=2.31.0        # HTTP requests for updates
setuptools>=67.0.0      # Package building tools
wheel>=0.40.0           # Python wheel packages
```

### Optional Dependencies

```txt
psutil>=5.9.0           # System and process monitoring (optional)
```

## Installation

### Method 1: From Source (Recommended for Development)

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Nsfr750/clamav-gui.git
   cd clamav-gui
   ```

2. **Create and activate virtual environment**:

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac (if using WSL or cross-platform)
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:

   ```bash
   python -m clamav_gui
   ```

### Method 2: Using pip (Production)

```bash
pip install clamav-gui
```

*Note: This method may not be available yet as the package isn't published to PyPI.*

## Development Setup

### Prerequisites for Development

- **Python 3.10+** with development headers
- **Git** for version control
- **ClamAV** for testing (optional but recommended)
- **Virtual Environment** tool

### Development Dependencies

```txt
pytest>=7.2.0           # Testing framework
pytest-cov>=4.0.0       # Coverage reporting
pytest-qt>=4.2.0        # Qt GUI testing
pytest-benchmark>=4.0.0 # Performance benchmarking
black>=22.10.0          # Code formatting
isort>=5.10.0           # Import sorting
mypy>=0.991             # Type checking
flake8>=5.0.0           # Linting
pre-commit>=3.0.0       # Git hooks
```

### Development Installation

1. **Install development dependencies**:

   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up pre-commit hooks**:

   ```bash
   pre-commit install
   ```

3. **Configure development environment**:

   ```bash
   # Copy environment template if it exists
   cp .env.example .env  # (if provided)

   # Set up IDE with Python type hints
   # Configure your IDE to use the virtual environment
   ```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=clamav_gui

# Run specific test categories
python -m pytest -m unit          # Unit tests
python -m pytest -m integration   # Integration tests
python -m pytest -m gui           # GUI tests
python -m pytest -m performance   # Performance tests

# Run tests with verbose output
python -m pytest -v
```

### Test Coverage

The project aims for comprehensive test coverage including:

- **Unit Tests**: Individual function and class testing
- **Integration Tests**: Component interaction testing
- **GUI Tests**: User interface testing with pytest-qt
- **Performance Tests**: Benchmarking and performance regression testing
- **Mock Testing**: ClamAV interaction isolation

## Building and Distribution

### Building from Source

```bash
# Install build dependencies
pip install build

# Build distribution packages
python -m build

# Build executable (Windows)
python build.py
```

### Installation Verification

After installation, verify the setup:

```bash
# Check if ClamAV GUI runs
python -m clamav_gui --version

# Test imports
python -c "import clamav_gui; print('Import successful')"

# Run basic functionality tests
python -m pytest tests/test_main.py -v
```

## Troubleshooting

### Common Issues

**Import Errors**:

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)
- Verify virtual environment activation

**ClamAV Not Found**:

- Install ClamAV from official sources
- Add ClamAV to system PATH
- Check antivirus settings if blocking ClamAV

**GUI Issues**:

- Update PySide6: `pip install --upgrade PySide6`
- Check display drivers and resolution settings
- Try running with different Qt backend

### Getting Help

- **Documentation**: Check `docs/` folder for detailed guides
- **Issues**: [GitHub Issues](https://github.com/Nsfr750/clamav-gui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Nsfr750/clamav-gui/discussions)
- **Email**: [nsfr750@yandex.com](mailto:nsfr750@yandex.com)

## Performance Considerations

### System Impact

- **CPU Usage**: Low to moderate during scans
- **Memory Usage**: ~50-100 MB baseline, up to 200 MB during intensive scans
- **Disk Usage**: Minimal, primarily for quarantine storage
- **Network Usage**: Low, mainly for virus database updates

### Optimization Tips

- Use SSD storage for better scan performance
- Close unnecessary applications during large scans
- Configure scan settings based on your security needs vs. performance requirements
- Regular virus database updates for optimal detection

## Security Considerations

### Data Protection

- All scanning operations are performed locally
- No personal data is transmitted externally
- Settings are stored locally in AppData directory
- Quarantine files are encrypted and stored locally

### Permissions

- Standard user permissions sufficient for most operations
- Administrative privileges may be needed for system-wide scans
- No unnecessary system access requested

## Contributing

For information on contributing to ClamAV GUI, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the GPLv3 License - see the [LICENSE](../LICENSE) file for details.

## Support

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and community support
- **Documentation**: Comprehensive guides in `docs/` folder

### Commercial Support

For commercial support or custom development:

- Email: [Nsfr750](mailto:nsfr750@yandex.com)
- Response time: Within 48 hours for inquiries
