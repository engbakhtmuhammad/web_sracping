#!/usr/bin/env python3
"""
Detailed Medicine Information Scraper for DVAGO.pk
=================================================

This module specializes in extracting comprehensive medicine information including:
- Detailed product descriptions
- Ingredients and dosage information
- Manufacturer and brand details
- Images and availability
- Reviews and ratings
- Alternative medicines and related products

Author: GitHub Copilot
Date: September 17, 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin
import logging
from tqdm import tqdm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class MedicineDetailScraper:
    """
    Specialized scraper for detailed medicine information
    """
    
    def __init__(self, base_scraper):
        """Initialize with reference to main scraper"""
        self.base_scraper = base_scraper
        self.base_url = base_scraper.base_url
        self.session = base_scraper.session
        self.logger = base_scraper.logger
        
    def extract_complete_medicine_info(self, product_url):
        """Extract comprehensive medicine information from product page"""
        self.logger.info(f"Extracting detailed medicine info from: {product_url}")
        
        # Use Selenium for dynamic content
        soup = self.base_scraper.make_request(product_url, use_selenium=True)
        if not soup:
            return None
        
        medicine_info = {
            'url': product_url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extract basic product information
        basic_info = self.extract_basic_info(soup)
        medicine_info.update(basic_info)
        
        # Extract pricing information
        pricing_info = self.extract_pricing_info(soup)
        medicine_info.update(pricing_info)
        
        # Extract medicine-specific information
        medical_info = self.extract_medical_info(soup)
        medicine_info.update(medical_info)
        
        # Extract images
        images = self.extract_product_images(soup)
        medicine_info['images'] = images
        
        # Extract availability and stock information
        availability_info = self.extract_availability_info(soup)
        medicine_info.update(availability_info)
        
        # Extract reviews and ratings
        review_info = self.extract_review_info(soup)
        medicine_info.update(review_info)
        
        # Extract related products
        related_products = self.extract_related_products(soup)
        medicine_info['related_products'] = related_products
        
        # Extract additional metadata
        metadata = self.extract_metadata(soup)
        medicine_info.update(metadata)
        
        return medicine_info
    
    def extract_basic_info(self, soup):
        """Extract basic product information"""
        info = {}
        
        # Product title/name
        title_selectors = [
            'h1',
            '.product-title',
            '.product-name',
            '[class*="title"]',
            '[class*="name"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                info['name'] = title_elem.get_text(strip=True)
                break
        
        # Product SKU/Code
        sku_patterns = [
            r'SKU[:\s]*([A-Za-z0-9-]+)',
            r'Product Code[:\s]*([A-Za-z0-9-]+)',
            r'Item Code[:\s]*([A-Za-z0-9-]+)'
        ]
        
        text_content = soup.get_text()
        for pattern in sku_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                info['sku'] = match.group(1).strip()
                break
        
        # Product description
        desc_selectors = [
            '.product-description',
            '.description',
            '.product-details',
            '[class*="description"]',
            '.product-info'
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                info['description'] = desc_elem.get_text(strip=True)
                break
        
        return info
    
    def extract_pricing_info(self, soup):
        """Extract comprehensive pricing information"""
        pricing = {
            'price_current': None,
            'price_original': None,
            'discount_percentage': None,
            'currency': 'PKR'
        }
        
        # Find all price elements
        price_texts = soup.find_all(text=re.compile(r'Rs\.\s*[\d,]+'))
        prices = []
        
        for price_text in price_texts:
            # Extract numerical value
            price_matches = re.findall(r'Rs\.\s*([\d,]+)', price_text)
            for match in price_matches:
                try:
                    price_value = float(match.replace(',', ''))
                    prices.append(price_value)
                except ValueError:
                    continue
        
        # Remove duplicates and sort
        unique_prices = sorted(list(set(prices)))
        
        if len(unique_prices) == 1:
            pricing['price_current'] = unique_prices[0]
        elif len(unique_prices) >= 2:
            # Usually current price is lower, original is higher
            pricing['price_current'] = unique_prices[0]
            pricing['price_original'] = unique_prices[-1]
            
            # Calculate discount
            if pricing['price_original'] > pricing['price_current']:
                discount = ((pricing['price_original'] - pricing['price_current']) / pricing['price_original']) * 100
                pricing['discount_percentage'] = round(discount, 2)
        
        # Look for specific price classes
        price_selectors = [
            '.current-price',
            '.sale-price',
            '.discounted-price',
            '.price-current'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'Rs\.\s*([\d,]+)', price_text)
                if price_match:
                    try:
                        pricing['price_current'] = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
                break
        
        return pricing
    
    def extract_medical_info(self, soup):
        """Extract medicine-specific information"""
        medical_info = {}
        
        text_content = soup.get_text()
        
        # Extract manufacturer/brand
        manufacturer_patterns = [
            r'Manufacturer[:\s]*([^\n]+)',
            r'Brand[:\s]*([^\n]+)',
            r'Company[:\s]*([^\n]+)',
            r'Made by[:\s]*([^\n]+)'
        ]
        
        for pattern in manufacturer_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                medical_info['manufacturer'] = match.group(1).strip()
                break
        
        # Extract ingredients/composition
        ingredient_patterns = [
            r'Ingredients[:\s]*([^\n]+)',
            r'Composition[:\s]*([^\n]+)',
            r'Active Ingredients[:\s]*([^\n]+)',
            r'Contains[:\s]*([^\n]+)'
        ]
        
        for pattern in ingredient_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                medical_info['ingredients'] = match.group(1).strip()
                break
        
        # Extract dosage information
        dosage_patterns = [
            r'Dosage[:\s]*([^\n]+)',
            r'Dose[:\s]*([^\n]+)',
            r'How to use[:\s]*([^\n]+)',
            r'Administration[:\s]*([^\n]+)'
        ]
        
        for pattern in dosage_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                medical_info['dosage'] = match.group(1).strip()
                break
        
        # Check if prescription is required
        prescription_keywords = [
            'prescription required',
            'prescription needed',
            'rx required',
            'doctor\'s prescription',
            'prescribed medicine'
        ]
        
        medical_info['prescription_required'] = any(
            keyword in text_content.lower() for keyword in prescription_keywords
        )
        
        # Extract medicine form
        form_patterns = [
            r'Form[:\s]*([^\n]+)',
            r'Type[:\s]*([^\n]+)',
            r'Formulation[:\s]*([^\n]+)'
        ]
        
        for pattern in form_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                medical_info['form'] = match.group(1).strip()
                break
        
        # Detect medicine form from title or description
        if 'form' not in medical_info:
            form_keywords = {
                'tablet': ['tablet', 'tab', 'pills'],
                'capsule': ['capsule', 'cap'],
                'syrup': ['syrup', 'liquid', 'suspension'],
                'injection': ['injection', 'inj', 'vial'],
                'cream': ['cream', 'ointment', 'gel'],
                'drops': ['drops', 'eye drops', 'ear drops']
            }
            
            title = medical_info.get('name', '').lower()
            desc = medical_info.get('description', '').lower()
            combined_text = f"{title} {desc}"
            
            for form_type, keywords in form_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    medical_info['form'] = form_type
                    break
        
        return medical_info
    
    def extract_product_images(self, soup):
        """Extract all product images"""
        images = []
        
        # Find all image tags
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            # Try different source attributes
            src_attrs = ['src', 'data-src', 'data-lazy-src', 'data-original']
            
            for attr in src_attrs:
                src = img.get(attr)
                if src and not src.startswith('data:'):
                    # Check if it's likely a product image
                    if any(keyword in src.lower() for keyword in ['product', 'medicine', 'dvago-assets']):
                        full_url = urljoin(self.base_url, src)
                        if full_url not in images:
                            images.append(full_url)
                    break
        
        return images
    
    def extract_availability_info(self, soup):
        """Extract availability and stock information"""
        availability = {
            'in_stock': True,
            'stock_quantity': None,
            'delivery_info': None
        }
        
        text_content = soup.get_text().lower()
        
        # Check stock status
        out_of_stock_keywords = [
            'out of stock',
            'not available',
            'unavailable',
            'sold out',
            'stock finished'
        ]
        
        if any(keyword in text_content for keyword in out_of_stock_keywords):
            availability['in_stock'] = False
        
        # Look for stock quantity
        stock_patterns = [
            r'(\d+)\s*in stock',
            r'stock:\s*(\d+)',
            r'available:\s*(\d+)',
            r'quantity:\s*(\d+)'
        ]
        
        for pattern in stock_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                try:
                    availability['stock_quantity'] = int(match.group(1))
                except ValueError:
                    pass
                break
        
        # Extract delivery information
        delivery_patterns = [
            r'delivery[:\s]*([^\n]+)',
            r'shipping[:\s]*([^\n]+)',
            r'arrives[:\s]*([^\n]+)'
        ]
        
        for pattern in delivery_patterns:
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                availability['delivery_info'] = match.group(1).strip()
                break
        
        return availability
    
    def extract_review_info(self, soup):
        """Extract review and rating information"""
        review_info = {
            'rating': None,
            'review_count': 0,
            'reviews': []
        }
        
        # Look for rating
        rating_selectors = [
            '.rating',
            '.stars',
            '[class*="rating"]',
            '[class*="star"]'
        ]
        
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                # Try to extract numerical rating
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                if rating_match:
                    try:
                        review_info['rating'] = float(rating_match.group(1))
                    except ValueError:
                        pass
                break
        
        # Look for review count
        review_count_patterns = [
            r'(\d+)\s*reviews?',
            r'(\d+)\s*ratings?',
            r'reviewed by\s*(\d+)'
        ]
        
        text_content = soup.get_text()
        for pattern in review_count_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                try:
                    review_info['review_count'] = int(match.group(1))
                except ValueError:
                    pass
                break
        
        return review_info
    
    def extract_related_products(self, soup):
        """Extract related or recommended products"""
        related_products = []
        
        # Look for related product sections
        related_sections = soup.find_all(['div', 'section'], 
                                       class_=re.compile(r'related|recommended|similar'))
        
        for section in related_sections:
            # Find product links in the section
            product_links = section.find_all('a', href=re.compile(r'/p/'))
            
            for link in product_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    name = link.get_text(strip=True)
                    
                    if name and len(name) > 2:
                        related_products.append({
                            'name': name,
                            'url': full_url
                        })
        
        return related_products
    
    def extract_metadata(self, soup):
        """Extract additional metadata"""
        metadata = {}
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                if 'description' in name.lower():
                    metadata['meta_description'] = content
                elif 'keywords' in name.lower():
                    metadata['meta_keywords'] = content
                elif 'title' in name.lower():
                    metadata['meta_title'] = content
        
        # Extract page title
        title_tag = soup.find('title')
        if title_tag:
            metadata['page_title'] = title_tag.get_text(strip=True)
        
        # Extract structured data (JSON-LD)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                metadata['structured_data'] = json_data
                break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return metadata
    
    def scrape_medicine_batch(self, product_urls, batch_size=10):
        """Scrape multiple medicines in batches"""
        self.logger.info(f"Scraping {len(product_urls)} medicines in batches of {batch_size}")
        
        all_medicines = []
        
        for i in range(0, len(product_urls), batch_size):
            batch = product_urls[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} medicines")
            
            batch_medicines = []
            for url in tqdm(batch, desc="Scraping medicines", leave=False):
                try:
                    medicine_info = self.extract_complete_medicine_info(url)
                    if medicine_info:
                        batch_medicines.append(medicine_info)
                    
                    # Delay between requests
                    time.sleep(self.base_scraper.delay)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping {url}: {str(e)}")
                    continue
            
            all_medicines.extend(batch_medicines)
            self.logger.info(f"Completed batch {i//batch_size + 1}: {len(batch_medicines)} medicines scraped")
            
            # Longer delay between batches
            time.sleep(self.base_scraper.delay * 2)
        
        self.logger.info(f"Completed scraping {len(all_medicines)} medicines")
        return all_medicines
    
    def save_medicine_details(self, medicines, output_file):
        """Save detailed medicine information to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(medicines, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(medicines)} detailed medicine records to {output_file}")


def test_medicine_scraper():
    """Test the medicine detail scraper"""
    from dvago_scraper import DvagoScraper
    
    # Initialize base scraper
    base_scraper = DvagoScraper(output_dir="test_output", delay=1.0)
    
    # Initialize medicine scraper
    medicine_scraper = MedicineDetailScraper(base_scraper)
    
    # Test URLs (replace with actual product URLs)
    test_urls = [
        "https://www.dvago.pk/p/panadol-500mg-tablets",
        "https://www.dvago.pk/p/risek-cap-20-mg-21s"
    ]
    
    print("Testing medicine detail extraction...")
    for url in test_urls:
        print(f"\nTesting: {url}")
        medicine_info = medicine_scraper.extract_complete_medicine_info(url)
        
        if medicine_info:
            print(f"Name: {medicine_info.get('name', 'N/A')}")
            print(f"Price: Rs. {medicine_info.get('price_current', 'N/A')}")
            print(f"Manufacturer: {medicine_info.get('manufacturer', 'N/A')}")
            print(f"Prescription Required: {medicine_info.get('prescription_required', 'N/A')}")
            print(f"In Stock: {medicine_info.get('in_stock', 'N/A')}")
        else:
            print("Failed to extract medicine information")


if __name__ == "__main__":
    test_medicine_scraper()