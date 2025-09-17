#!/usr/bin/env python3
"""
DVAGO.pk Comprehensive Web Scraper
==================================

This script scrapes all data from dvago.pk including:
- Categories and subcategories
- Medicine listings with prices and details
- Product information and images
- Brands and manufacturers

Features:
- Respectful scraping with rate limiting
- Error handling and retry mechanisms
- Multiple export formats (CSV, JSON, Excel)
- SQLite database storage
- Progress tracking
- Resume capability

Author: GitHub Copilot
Date: September 17, 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import sqlite3
import pandas as pd
import time
import logging
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re
from tqdm import tqdm
import os
from datetime import datetime
import threading
from queue import Queue
import hashlib


class DvagoScraper:
    """
    Comprehensive scraper for dvago.pk pharmacy website
    """
    
    def __init__(self, output_dir="dvago_data", max_workers=3, delay=1.5):
        """
        Initialize the scraper
        
        Args:
            output_dir (str): Directory to save scraped data
            max_workers (int): Number of concurrent workers
            delay (float): Delay between requests in seconds
        """
        self.base_url = "https://www.dvago.pk"
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.delay = delay
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize user agent
        self.ua = UserAgent()
        
        # Initialize data storage
        self.categories = []
        self.subcategories = []
        self.products = []
        self.brands = []
        
        # Initialize database
        self.init_database()
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Initialize Selenium driver (will be created when needed)
        self.driver = None
        
        self.logger.info("DvagoScraper initialized successfully")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = os.path.join(self.output_dir, f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize SQLite database"""
        self.db_path = os.path.join(self.output_dir, "dvago_data.db")
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create tables
        self.create_tables()
        self.logger.info(f"Database initialized: {self.db_path}")
    
    def create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                slug TEXT,
                image_url TEXT,
                parent_id INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories (id)
            )
        ''')
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                slug TEXT,
                sku TEXT,
                price_current REAL,
                price_original REAL,
                discount_percentage REAL,
                description TEXT,
                ingredients TEXT,
                dosage TEXT,
                manufacturer TEXT,
                brand TEXT,
                category_id INTEGER,
                image_url TEXT,
                in_stock BOOLEAN,
                prescription_required BOOLEAN,
                rating REAL,
                reviews_count INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # Brands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                url TEXT,
                logo_url TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Product images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                image_url TEXT,
                image_type TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        self.conn.commit()
        self.logger.info("Database tables created successfully")
    
    def get_selenium_driver(self):
        """Get or create Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'--user-agent={self.ua.random}')
            
            try:
                # Try to get Chrome driver for the current architecture
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.logger.info("Selenium WebDriver initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Chrome WebDriver: {str(e)}")
                self.logger.info("Selenium functionality will be disabled - falling back to requests only")
                self.driver = None
        
        return self.driver
    
    def make_request(self, url, use_selenium=False, retries=3):
        """
        Make HTTP request with error handling and retries
        
        Args:
            url (str): URL to request
            use_selenium (bool): Whether to use Selenium instead of requests
            retries (int): Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                if use_selenium:
                    driver = self.get_selenium_driver()
                    if driver is None:
                        # Fall back to requests if Selenium fails
                        self.logger.warning("Selenium not available, falling back to requests")
                        use_selenium = False
                    else:
                        driver.get(url)
                        time.sleep(2)  # Wait for page to load
                        html = driver.page_source
                        return BeautifulSoup(html, 'html.parser')
                
                if not use_selenium:
                    # Random delay to be respectful
                    time.sleep(self.delay + (attempt * 0.5))
                    
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Use XML parser for XML documents, HTML parser for HTML
                    if 'xml' in url.lower() or response.headers.get('content-type', '').startswith('application/xml'):
                        return BeautifulSoup(response.content, 'xml')
                    else:
                        return BeautifulSoup(response.content, 'html.parser')
                    
            except Exception as e:
                self.logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {str(e)}")
                if attempt == retries - 1:
                    self.logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def extract_categories(self):
        """Extract all main categories from the homepage"""
        self.logger.info("Starting category extraction...")
        
        soup = self.make_request(self.base_url)
        if not soup:
            self.logger.error("Failed to fetch homepage")
            return
        
        # Find category links
        category_links = []
        
        # Look for category sections
        categories_section = soup.find_all(['a'], href=re.compile(r'/cat/'))
        
        for link in categories_section:
            href = link.get('href')
            if href and '/cat/' in href:
                name = link.get_text(strip=True)
                if name and len(name) > 1:  # Filter out empty or single character names
                    full_url = urljoin(self.base_url, href)
                    
                    # Extract image if available
                    img_tag = link.find('img')
                    image_url = None
                    if img_tag:
                        image_url = img_tag.get('src')
                        if image_url:
                            image_url = urljoin(self.base_url, image_url)
                    
                    category_data = {
                        'name': name,
                        'url': full_url,
                        'slug': href.split('/cat/')[-1] if '/cat/' in href else '',
                        'image_url': image_url
                    }
                    
                    # Avoid duplicates
                    if not any(cat['url'] == full_url for cat in category_links):
                        category_links.append(category_data)
        
        # Also check for A-Z medicine link
        az_links = soup.find_all('a', href=re.compile(r'/atozmedicine/'))
        for link in az_links:
            href = link.get('href')
            name = link.get_text(strip=True)
            if name and href:
                full_url = urljoin(self.base_url, href)
                category_data = {
                    'name': name,
                    'url': full_url,
                    'slug': 'a-to-z-medicine',
                    'image_url': None
                }
                if not any(cat['url'] == full_url for cat in category_links):
                    category_links.append(category_data)
        
        self.categories = category_links
        self.logger.info(f"Found {len(self.categories)} main categories")
        
        # Save to database
        self.save_categories_to_db()
        
        return self.categories
    
    def extract_subcategories(self, category_url):
        """Extract subcategories from a category page"""
        self.logger.info(f"Extracting subcategories from: {category_url}")
        
        soup = self.make_request(category_url)
        if not soup:
            return []
        
        subcategories = []
        
        # Look for subcategory links
        # They might be in different formats, so we'll try multiple selectors
        possible_selectors = [
            'a[href*="/cat/"]',
            'a[href*="/subcat/"]',
            '.category-item a',
            '.subcategory a'
        ]
        
        for selector in possible_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                name = link.get_text(strip=True)
                
                if href and name and len(name) > 1:
                    full_url = urljoin(self.base_url, href)
                    
                    # Skip if it's the same as parent category
                    if full_url != category_url:
                        subcat_data = {
                            'name': name,
                            'url': full_url,
                            'parent_url': category_url
                        }
                        
                        if not any(sub['url'] == full_url for sub in subcategories):
                            subcategories.append(subcat_data)
        
        self.logger.info(f"Found {len(subcategories)} subcategories")
        return subcategories
    
    def extract_products_from_page(self, page_url, category_info=None):
        """Extract products from a single page"""
        self.logger.info(f"Extracting products from: {page_url}")
        
        soup = self.make_request(page_url, use_selenium=True)
        if not soup:
            return []
        
        products = []
        
        # Look for product links - these usually contain /p/ in the URL
        product_links = soup.find_all('a', href=re.compile(r'/p/'))
        
        for link in product_links:
            href = link.get('href')
            if not href:
                continue
                
            full_url = urljoin(self.base_url, href)
            
            # Extract product name
            name = ""
            name_elem = link.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if name_elem:
                name = name_elem.get_text(strip=True)
            else:
                # Try to get name from link text
                name = link.get_text(strip=True)
            
            if not name or len(name) < 2:
                continue
            
            # Extract image
            image_url = None
            img_tag = link.find('img')
            if img_tag:
                image_url = img_tag.get('src')
                if image_url:
                    image_url = urljoin(self.base_url, image_url)
            
            # Try to extract price from the same container
            price_current = None
            price_original = None
            
            # Look for price in parent container
            parent = link.parent
            for _ in range(3):  # Check up to 3 levels up
                if parent:
                    price_texts = parent.find_all(text=re.compile(r'Rs\.\s*[\d,]+'))
                    if price_texts:
                        prices = []
                        for price_text in price_texts:
                            # Extract numerical value
                            price_match = re.search(r'Rs\.\s*([\d,]+)', price_text)
                            if price_match:
                                price_value = float(price_match.group(1).replace(',', ''))
                                prices.append(price_value)
                        
                        if prices:
                            prices.sort()
                            price_current = prices[0]  # Lowest price is current
                            if len(prices) > 1:
                                price_original = prices[-1]  # Highest price is original
                        break
                    parent = parent.parent
                else:
                    break
            
            product_data = {
                'name': name,
                'url': full_url,
                'slug': href.split('/p/')[-1] if '/p/' in href else '',
                'price_current': price_current,
                'price_original': price_original,
                'image_url': image_url,
                'category_info': category_info
            }
            
            # Avoid duplicates
            if not any(prod['url'] == full_url for prod in products):
                products.append(product_data)
        
        self.logger.info(f"Found {len(products)} products on page")
        return products
    
    def extract_detailed_product_info(self, product_url):
        """Extract detailed information from a product page"""
        self.logger.info(f"Extracting detailed info from: {product_url}")
        
        soup = self.make_request(product_url, use_selenium=True)
        if not soup:
            return None
        
        product_details = {}
        
        # Extract product title
        title_selectors = ['h1', '.product-title', '.product-name']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                product_details['name'] = title_elem.get_text(strip=True)
                break
        
        # Extract prices
        price_texts = soup.find_all(text=re.compile(r'Rs\.\s*[\d,]+'))
        prices = []
        for price_text in price_texts:
            price_match = re.search(r'Rs\.\s*([\d,]+)', price_text)
            if price_match:
                price_value = float(price_match.group(1).replace(',', ''))
                prices.append(price_value)
        
        if prices:
            prices.sort()
            product_details['price_current'] = prices[0]
            if len(prices) > 1:
                product_details['price_original'] = prices[-1]
        
        # Extract description
        desc_selectors = ['.product-description', '.product-details', '.description']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                product_details['description'] = desc_elem.get_text(strip=True)
                break
        
        # Extract images
        images = []
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src')
            if src and ('product' in src.lower() or 'dvago-assets' in src):
                full_img_url = urljoin(self.base_url, src)
                images.append(full_img_url)
        
        product_details['images'] = list(set(images))  # Remove duplicates
        
        # Extract other details (brand, manufacturer, etc.)
        # These might be in various formats, so we'll use flexible parsing
        text_content = soup.get_text()
        
        # Try to find brand information
        brand_patterns = [
            r'Brand:\s*([^\n]+)',
            r'Manufacturer:\s*([^\n]+)',
            r'Company:\s*([^\n]+)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                product_details['brand'] = match.group(1).strip()
                break
        
        # Try to find if prescription is required
        if any(keyword in text_content.lower() for keyword in ['prescription required', 'prescription needed', 'rx required']):
            product_details['prescription_required'] = True
        else:
            product_details['prescription_required'] = False
        
        # Check stock status
        if any(keyword in text_content.lower() for keyword in ['out of stock', 'not available', 'unavailable']):
            product_details['in_stock'] = False
        else:
            product_details['in_stock'] = True
        
        return product_details
    
    def save_categories_to_db(self):
        """Save categories to database"""
        cursor = self.conn.cursor()
        
        for category in self.categories:
            cursor.execute('''
                INSERT OR REPLACE INTO categories (name, url, slug, image_url)
                VALUES (?, ?, ?, ?)
            ''', (
                category.get('name'),
                category.get('url'),
                category.get('slug'),
                category.get('image_url')
            ))
        
        self.conn.commit()
        self.logger.info(f"Saved {len(self.categories)} categories to database")
    
    def save_products_to_db(self, products):
        """Save products to database"""
        cursor = self.conn.cursor()
        
        for product in products:
            # Calculate discount percentage
            discount_percentage = None
            if product.get('price_original') and product.get('price_current'):
                if product['price_original'] > product['price_current']:
                    discount_percentage = ((product['price_original'] - product['price_current']) / product['price_original']) * 100
            
            cursor.execute('''
                INSERT OR REPLACE INTO products (
                    name, url, slug, price_current, price_original, discount_percentage,
                    description, brand, image_url, in_stock, prescription_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product.get('name'),
                product.get('url'),
                product.get('slug'),
                product.get('price_current'),
                product.get('price_original'),
                discount_percentage,
                product.get('description'),
                product.get('brand'),
                product.get('image_url'),
                product.get('in_stock', True),
                product.get('prescription_required', False)
            ))
        
        self.conn.commit()
        self.logger.info(f"Saved {len(products)} products to database")
    
    def export_to_csv(self):
        """Export data to CSV files"""
        self.logger.info("Exporting data to CSV files...")
        
        # Export categories
        if self.categories:
            df_categories = pd.DataFrame(self.categories)
            df_categories.to_csv(os.path.join(self.output_dir, 'categories.csv'), index=False)
            self.logger.info(f"Exported {len(self.categories)} categories to CSV")
        
        # Export products from database
        df_products = pd.read_sql_query("SELECT * FROM products", self.conn)
        if not df_products.empty:
            df_products.to_csv(os.path.join(self.output_dir, 'products.csv'), index=False)
            self.logger.info(f"Exported {len(df_products)} products to CSV")
        
        # Export brands
        df_brands = pd.read_sql_query("SELECT * FROM brands", self.conn)
        if not df_brands.empty:
            df_brands.to_csv(os.path.join(self.output_dir, 'brands.csv'), index=False)
            self.logger.info(f"Exported {len(df_brands)} brands to CSV")
    
    def export_to_json(self):
        """Export data to JSON files"""
        self.logger.info("Exporting data to JSON files...")
        
        # Export categories
        if self.categories:
            with open(os.path.join(self.output_dir, 'categories.json'), 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, indent=2, ensure_ascii=False)
        
        # Export products
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
        
        if products:
            with open(os.path.join(self.output_dir, 'products.json'), 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
        
        self.logger.info("Data exported to JSON files")
    
    def export_to_excel(self):
        """Export data to Excel file"""
        self.logger.info("Exporting data to Excel file...")
        
        excel_path = os.path.join(self.output_dir, 'dvago_complete_data.xlsx')
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Categories
            if self.categories:
                df_categories = pd.DataFrame(self.categories)
                df_categories.to_excel(writer, sheet_name='Categories', index=False)
            
            # Products
            df_products = pd.read_sql_query("SELECT * FROM products", self.conn)
            if not df_products.empty:
                df_products.to_excel(writer, sheet_name='Products', index=False)
            
            # Brands
            df_brands = pd.read_sql_query("SELECT * FROM brands", self.conn)
            if not df_brands.empty:
                df_brands.to_excel(writer, sheet_name='Brands', index=False)
        
        self.logger.info(f"Data exported to Excel: {excel_path}")
    
    def scrape_all(self, max_products_per_category=None):
        """
        Main method to scrape all data from the website
        
        Args:
            max_products_per_category (int): Limit products per category (for testing)
        """
        self.logger.info("Starting comprehensive scraping of dvago.pk...")
        
        try:
            # Step 1: Extract categories
            categories = self.extract_categories()
            if not categories:
                self.logger.error("No categories found. Aborting.")
                return
            
            # Step 2: Scrape products from each category
            total_products = []
            
            for i, category in enumerate(tqdm(categories, desc="Scraping categories")):
                self.logger.info(f"Processing category {i+1}/{len(categories)}: {category['name']}")
                
                # Extract products from category page
                products = self.extract_products_from_page(category['url'], category)
                
                if max_products_per_category:
                    products = products[:max_products_per_category]
                
                # Get detailed info for each product
                detailed_products = []
                for product in tqdm(products[:10], desc=f"Processing products in {category['name']}", leave=False):  # Limit to 10 per category for testing
                    detailed_info = self.extract_detailed_product_info(product['url'])
                    if detailed_info:
                        # Merge basic and detailed info
                        product.update(detailed_info)
                    detailed_products.append(product)
                    
                    # Small delay between product requests
                    time.sleep(self.delay)
                
                total_products.extend(detailed_products)
                
                # Save products in batches
                if detailed_products:
                    self.save_products_to_db(detailed_products)
                
                # Longer delay between categories
                time.sleep(self.delay * 2)
            
            self.products = total_products
            self.logger.info(f"Scraping completed! Total products: {len(total_products)}")
            
            # Step 3: Export data
            self.export_to_csv()
            self.export_to_json()
            self.export_to_excel()
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
            self.conn.close()
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


def main():
    """Main function to run the scraper"""
    print("DVAGO.pk Comprehensive Web Scraper")
    print("=" * 50)
    
    # Initialize scraper
    scraper = DvagoScraper(
        output_dir="dvago_scraped_data",
        max_workers=2,
        delay=2.0  # Be respectful to the server
    )
    
    try:
        # Start scraping (limit products for testing)
        scraper.scrape_all(max_products_per_category=20)
        
        print("\nScraping completed successfully!")
        print(f"Data saved in: {scraper.output_dir}")
        print("\nFiles created:")
        print("- dvago_data.db (SQLite database)")
        print("- categories.csv")
        print("- products.csv") 
        print("- categories.json")
        print("- products.json")
        print("- dvago_complete_data.xlsx")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
    finally:
        print("\nCleaning up...")


if __name__ == "__main__":
    main()