# ClamAV GUI - Requirements

## System Requirements

- Windows 10/11 (64-bit)
- Python 3.9 or higher
- ClamAV Antivirus
- Git

## Python Dependencies

### Core Dependencies
- PyQt6 >= 6.4.0
- clamd >= 1.0.2
- python-dotenv >= 0.21.0
- psutil >= 5.9.0

### Development Dependencies
- black >= 22.10.0
- pytest >= 7.2.0
- pytest-qt >= 4.2.0
- pylint >= 2.15.0
- mypy >= 0.991

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Nsfr750/clamav-gui.git
   cd clamav-gui
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Configure pre-commit hooks:
   ```bash
   pre-commit install
   ```

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on [GitHub](https://github.com/Nsfr750/clamav-gui/issues) or join our [Discord](https://discord.gg/ryqNeuRYjD).

## Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Donate

If you find this project useful, consider supporting it:
- [PayPal](https://paypal.me/3dmega)
- [Patreon](https://www.patreon.com/Nsfr750)
- Monero: `47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSxDrnCUBJ5WBj6Fgmsfix8VPD4w3gXF`

---

© Copyright 2025 Nsfr750 - All rights reserved
