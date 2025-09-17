# DVAGO.pk Complete Web Scraper

A comprehensive web scraping solution for dvago.pk that extracts all categories, subcategories, medicines, and product information with multiple export formats.

## 🚀 Features

- **Complete Website Coverage**: Scrapes all categories, subcategories, and products
- **Intelligent Category Discovery**: Finds all categories including hidden ones
- **Detailed Medicine Information**: Extracts comprehensive medicine details including ingredients, dosage, manufacturer, etc.
- **Multiple Export Formats**: CSV, JSON, Excel, XML, and SQLite database
- **Respectful Scraping**: Rate limiting and delay controls to be respectful to the server
- **Error Handling**: Robust error handling with retry mechanisms
- **Progress Tracking**: Save and resume scraping sessions
- **Data Validation**: Automatic data cleaning and validation
- **Comprehensive Reporting**: Detailed reports and analytics

## 📋 Requirements

- Python 3.8+
- Chrome browser (for Selenium)
- Internet connection

## 🛠️ Installation

1. **Clone or download the project files to your directory**

2. **Install required packages** (automatically handled by the scraper):
   ```bash
   # The scraper will automatically install these packages:
   # requests, beautifulsoup4, selenium, pandas, lxml, openpyxl
   # fake-useragent, webdriver-manager, tqdm, urllib3
   ```

3. **Make sure Chrome browser is installed** (required for Selenium)

## 🏃‍♂️ Quick Start

### Basic Usage

```bash
# Run the complete scraper with default settings
python main_scraper.py

# Run tests first to validate setup
python test_scraper.py
```

### Advanced Usage

```bash
# Custom output directory
python main_scraper.py --output-dir my_data

# Slower scraping (more respectful to server)
python main_scraper.py --delay 3.0

# Limit products per category (for testing)
python main_scraper.py --max-products 50

# Skip detailed medicine information extraction
python main_scraper.py --no-detailed

# Resume interrupted session
python main_scraper.py --resume
```

## 📁 Project Structure

```
web_scraping/
├── main_scraper.py              # Main entry point
├── dvago_scraper.py             # Core scraper framework
├── advanced_scraper.py          # Advanced category and product extraction
├── medicine_detail_scraper.py   # Detailed medicine information extraction
├── data_export_manager.py       # Data export and management
├── test_scraper.py              # Test suite
└── README.md                    # This file
```

## 📊 Output Data Structure

The scraper generates the following data files:

### Database Tables (SQLite)
- **categories**: All discovered categories and subcategories
- **products**: Complete product information
- **brands**: Manufacturer and brand information
- **product_images**: Product image URLs

### Export Files
- **CSV files**: Individual tables in CSV format
- **JSON files**: Structured data in JSON format
- **Excel file**: Multi-sheet workbook with all data
- **XML files**: XML formatted data exports
- **HTML report**: Comprehensive scraping report

## 🗂️ Data Fields

### Categories
- `id`, `name`, `url`, `slug`, `image_url`, `parent_id`

### Products
- `id`, `name`, `url`, `slug`, `sku`
- `price_current`, `price_original`, `discount_percentage`
- `description`, `ingredients`, `dosage`
- `manufacturer`, `brand`, `category_id`
- `image_url`, `in_stock`, `prescription_required`
- `rating`, `reviews_count`, `scraped_at`

### Detailed Medicine Information
- All product fields plus:
- `form` (tablet, syrup, injection, etc.)
- `meta_description`, `meta_keywords`
- `related_products`, `images` (array)
- `structured_data`, `availability_info`

## ⚙️ Configuration Options

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--output-dir` | `dvago_complete_data` | Output directory for all data |
| `--delay` | `2.0` | Delay between requests (seconds) |
| `--max-products` | `None` | Max products per category (for testing) |
| `--no-detailed` | `False` | Skip detailed medicine extraction |
| `--resume` | `False` | Resume from previous session |

### Internal Configuration

You can modify these settings in the code:

```python
config = {
    'output_dir': 'dvago_complete_data',
    'delay': 2.0,  # Seconds between requests
    'max_products_per_category': None,  # None = unlimited
    'detailed_scraping': True,  # Extract detailed medicine info
    'max_workers': 2,  # Concurrent workers
}
```

## 🧪 Testing

Run the test suite to validate your setup:

```bash
python test_scraper.py
```

The test suite validates:
- Basic scraper functionality
- Category discovery
- Product extraction
- Medicine detail extraction
- Database operations

## 📈 Performance & Scaling

### Recommended Settings for Different Use Cases

**Full Production Scrape** (respectful, complete):
```bash
python main_scraper.py --delay 2.0
```

**Fast Testing** (limited scope):
```bash
python main_scraper.py --delay 1.0 --max-products 10 --no-detailed
```

**Comprehensive Research** (detailed extraction):
```bash
python main_scraper.py --delay 3.0
```

### Performance Considerations

- **Memory Usage**: ~100-500MB depending on data size
- **Disk Space**: ~50-200MB for complete dataset
- **Time**: 2-6 hours for complete scraping (depends on delay settings)
- **Network**: Respectful rate limiting prevents server overload

## 🛡️ Ethical Considerations

This scraper is designed to be respectful and ethical:

- **Rate Limiting**: Built-in delays between requests
- **Error Handling**: Graceful handling of failures
- **User Agent Rotation**: Prevents detection as bot
- **Respectful Scraping**: Follows robots.txt guidelines
- **No Overloading**: Limited concurrent requests

## 📄 Legal Disclaimer

This tool is provided for educational and research purposes only. Users are responsible for:

- Complying with dvago.pk's Terms of Service
- Respecting robots.txt directives
- Using scraped data ethically and legally
- Not overloading the target server

## 🔧 Troubleshooting

### Common Issues

**Chrome Driver Issues**:
```bash
# The scraper automatically downloads Chrome driver
# If issues persist, ensure Chrome browser is installed
```

**Memory Issues**:
```bash
# Reduce batch size or add delays
python main_scraper.py --delay 3.0 --max-products 20
```

**Network Errors**:
```bash
# Increase delay and retry
python main_scraper.py --delay 5.0
```

**Permission Errors**:
```bash
# Ensure write permissions to output directory
chmod 755 dvago_complete_data/
```

### Debug Mode

Enable detailed logging by modifying the log level in the code:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📧 Support

For issues or questions:

1. Check the troubleshooting section above
2. Run the test suite: `python test_scraper.py`
3. Review log files in the `logs/` directory
4. Check the generated HTML report for data quality issues

## 🔄 Updates and Maintenance

The scraper is designed to be resilient to website changes, but may need updates if:

- Website structure changes significantly
- New product categories are added
- Anti-bot measures are implemented

## 📊 Sample Output

After running the scraper, you'll find:

```
dvago_complete_data/
├── dvago_data.db                 # SQLite database
├── csv_exports/
│   ├── categories_20250917.csv
│   ├── products_20250917.csv
│   └── brands_20250917.csv
├── json_exports/
│   ├── categories_20250917.json
│   └── products_20250917.json
├── excel_exports/
│   └── dvago_complete_data_20250917.xlsx
├── reports/
│   └── data_report_20250917.html
├── logs/
│   └── complete_scraper_20250917.log
└── scraping_progress.json        # Progress tracking
```

## 🎯 Use Cases

- **Market Research**: Analyze medicine prices and availability
- **Competitive Analysis**: Compare product offerings
- **Data Analysis**: Research healthcare product trends
- **Academic Research**: Study e-commerce in healthcare
- **Business Intelligence**: Market insights and pricing strategies

---

**Note**: Always ensure you have permission to scrape the target website and comply with their terms of service and robots.txt file.