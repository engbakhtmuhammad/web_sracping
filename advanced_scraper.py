#!/usr/bin/env python3
"""
Enhanced Category and Product Scraper for DVAGO.pk
=================================================

This module provides specialized functions for:
- Discovering all categories and subcategories
- Handling pagination
- Extracting comprehensive product information
- Managing A-Z medicine listings

Author: GitHub Copilot
Date: September 17, 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs
from fake_useragent import UserAgent
import logging
from tqdm import tqdm


class AdvancedDvagoScraper:
    """
    Advanced scraper with enhanced category and product extraction
    """
    
    def __init__(self, base_scraper):
        """Initialize with reference to main scraper"""
        self.base_scraper = base_scraper
        self.base_url = base_scraper.base_url
        self.session = base_scraper.session
        self.logger = base_scraper.logger
        
    def discover_all_categories(self):
        """Discover all categories including hidden ones"""
        self.logger.info("Starting comprehensive category discovery...")
        
        all_categories = []
        
        # 1. Get main page categories
        main_categories = self.extract_homepage_categories()
        all_categories.extend(main_categories)
        
        # 2. Get categories from sitemap or category listing page
        sitemap_categories = self.extract_from_sitemap()
        all_categories.extend(sitemap_categories)
        
        # 3. Get A-Z medicine categories
        az_categories = self.extract_az_medicine_categories()
        all_categories.extend(az_categories)
        
        # 4. Get categories from footer and navigation
        nav_categories = self.extract_navigation_categories()
        all_categories.extend(nav_categories)
        
        # Remove duplicates
        unique_categories = []
        seen_urls = set()
        
        for cat in all_categories:
            if cat['url'] not in seen_urls:
                unique_categories.append(cat)
                seen_urls.add(cat['url'])
        
        self.logger.info(f"Discovered {len(unique_categories)} unique categories")
        return unique_categories
    
    def extract_homepage_categories(self):
        """Extract categories from homepage"""
        soup = self.base_scraper.make_request(self.base_url)
        if not soup:
            return []
        
        categories = []
        
        # Look for category containers
        category_selectors = [
            'a[href*="/cat/"]',
            'a[href*="/atozmedicine/"]',
            '.category-item a',
            '.category-card a',
            '[class*="category"] a'
        ]
        
        for selector in category_selectors:
            links = soup.select(selector)
            for link in links:
                category = self.extract_category_info(link)
                if category:
                    categories.append(category)
        
        return categories
    
    def extract_from_sitemap(self):
        """Try to extract categories from sitemap"""
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap",
            f"{self.base_url}/categories"
        ]
        
        categories = []
        
        for sitemap_url in sitemap_urls:
            try:
                soup = self.base_scraper.make_request(sitemap_url)
                if soup:
                    # Look for category URLs in sitemap
                    links = soup.find_all(['url', 'a'])
                    for link in links:
                        if link.name == 'url':
                            loc = link.find('loc')
                            if loc and '/cat/' in loc.get_text():
                                url = loc.get_text()
                                name = url.split('/cat/')[-1].replace('-', ' ').title()
                                categories.append({
                                    'name': name,
                                    'url': url,
                                    'slug': url.split('/cat/')[-1],
                                    'image_url': None,
                                    'source': 'sitemap'
                                })
                        elif link.get('href') and '/cat/' in link.get('href'):
                            category = self.extract_category_info(link)
                            if category:
                                categories.append(category)
                break
            except:
                continue
        
        return categories
    
    def extract_az_medicine_categories(self):
        """Extract A-Z medicine categories"""
        categories = []
        
        # Create A-Z categories
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            categories.append({
                'name': f"Medicines starting with {letter}",
                'url': f"{self.base_url}/atozmedicine/{letter}",
                'slug': f"medicine-{letter.lower()}",
                'image_url': None,
                'parent_category': 'A to Z Medicine',
                'source': 'a-z-medicine'
            })
        
        return categories
    
    def extract_navigation_categories(self):
        """Extract categories from navigation menus"""
        soup = self.base_scraper.make_request(self.base_url)
        if not soup:
            return []
        
        categories = []
        
        # Look in navigation areas
        nav_areas = soup.find_all(['nav', 'header', 'footer'])
        
        for nav in nav_areas:
            links = nav.find_all('a', href=re.compile(r'/cat/|/atozmedicine/'))
            for link in links:
                category = self.extract_category_info(link)
                if category:
                    categories.append(category)
        
        return categories
    
    def extract_category_info(self, link_element):
        """Extract category information from a link element"""
        href = link_element.get('href')
        if not href:
            return None
        
        # Clean and validate URL
        if href.startswith('/'):
            full_url = urljoin(self.base_url, href)
        else:
            full_url = href
        
        # Get category name
        name = link_element.get_text(strip=True)
        if not name or len(name) < 2:
            # Try to get name from title or alt attributes
            name = link_element.get('title') or link_element.get('alt') or ''
            if not name:
                # Extract from URL
                if '/cat/' in href:
                    name = href.split('/cat/')[-1].replace('-', ' ').title()
                elif '/atozmedicine/' in href:
                    letter = href.split('/atozmedicine/')[-1]
                    name = f"Medicines - {letter}"
        
        if not name or len(name) < 2:
            return None
        
        # Extract image URL
        image_url = None
        img_tag = link_element.find('img')
        if img_tag:
            image_url = img_tag.get('src') or img_tag.get('data-src')
            if image_url:
                image_url = urljoin(self.base_url, image_url)
        
        # Extract slug
        slug = ''
        if '/cat/' in href:
            slug = href.split('/cat/')[-1]
        elif '/atozmedicine/' in href:
            slug = 'atozmedicine-' + href.split('/atozmedicine/')[-1]
        
        return {
            'name': name,
            'url': full_url,
            'slug': slug,
            'image_url': image_url,
            'source': 'navigation'
        }
    
    def discover_subcategories(self, category_url):
        """Discover subcategories within a category"""
        self.logger.info(f"Discovering subcategories for: {category_url}")
        
        soup = self.base_scraper.make_request(category_url, use_selenium=True)
        if not soup:
            return []
        
        subcategories = []
        
        # Look for subcategory links
        subcategory_selectors = [
            'a[href*="/cat/"]',
            '.subcategory a',
            '.filter a',
            '.category-filter a'
        ]
        
        for selector in subcategory_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and href != category_url:
                    subcat = self.extract_category_info(link)
                    if subcat:
                        subcat['parent_url'] = category_url
                        subcategories.append(subcat)
        
        return subcategories
    
    def extract_products_with_pagination(self, category_url, max_pages=None):
        """Extract all products from a category with pagination handling"""
        self.logger.info(f"Extracting products with pagination from: {category_url}")
        
        all_products = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            # Construct page URL
            if '?' in category_url:
                page_url = f"{category_url}&page={page}"
            else:
                page_url = f"{category_url}?page={page}"
            
            self.logger.info(f"Scraping page {page}: {page_url}")
            
            # Get products from current page
            products = self.extract_products_from_page(page_url)
            
            if not products:
                self.logger.info(f"No products found on page {page}, stopping pagination")
                break
            
            all_products.extend(products)
            self.logger.info(f"Found {len(products)} products on page {page}")
            
            # Check if there's a next page
            if not self.has_next_page(page_url):
                self.logger.info("No more pages found")
                break
            
            page += 1
            time.sleep(self.base_scraper.delay)
        
        self.logger.info(f"Total products extracted: {len(all_products)}")
        return all_products
    
    def has_next_page(self, current_page_url):
        """Check if there's a next page"""
        soup = self.base_scraper.make_request(current_page_url)
        if not soup:
            return False
        
        # Look for pagination indicators
        next_indicators = [
            'a[href*="page="]:contains("Next")',
            'a[href*="page="]:contains(">")',
            '.pagination a[href*="page="]',
            '.next-page',
            '[class*="next"]'
        ]
        
        for indicator in next_indicators:
            if soup.select(indicator):
                return True
        
        return False
    
    def extract_products_from_page(self, page_url):
        """Enhanced product extraction from a single page"""
        soup = self.base_scraper.make_request(page_url, use_selenium=True)
        if not soup:
            return []
        
        products = []
        
        # Multiple strategies to find products
        product_selectors = [
            'a[href*="/p/"]',
            '.product-item a',
            '.product-card a',
            '[class*="product"] a[href*="/p/"]'
        ]
        
        found_products = set()
        
        for selector in product_selectors:
            product_links = soup.select(selector)
            
            for link in product_links:
                href = link.get('href')
                if not href or href in found_products:
                    continue
                
                found_products.add(href)
                
                product = self.extract_product_summary(link, soup)
                if product:
                    products.append(product)
        
        return products
    
    def extract_product_summary(self, link_element, page_soup):
        """Extract product summary information from link element"""
        href = link_element.get('href')
        if not href:
            return None
        
        full_url = urljoin(self.base_url, href)
        
        # Extract product name
        name = self.extract_product_name(link_element)
        if not name:
            return None
        
        # Extract prices
        prices = self.extract_product_prices(link_element, page_soup)
        
        # Extract image
        image_url = self.extract_product_image(link_element)
        
        # Extract additional info
        additional_info = self.extract_additional_product_info(link_element)
        
        product = {
            'name': name,
            'url': full_url,
            'slug': href.split('/p/')[-1] if '/p/' in href else '',
            'image_url': image_url,
            **prices,
            **additional_info
        }
        
        return product
    
    def extract_product_name(self, link_element):
        """Extract product name from various sources"""
        # Try different methods to get product name
        name_sources = [
            lambda: link_element.get_text(strip=True),
            lambda: link_element.get('title'),
            lambda: link_element.get('alt'),
            lambda: link_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']).get_text(strip=True) if link_element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) else None,
            lambda: link_element.find(class_=re.compile(r'name|title')).get_text(strip=True) if link_element.find(class_=re.compile(r'name|title')) else None
        ]
        
        for source in name_sources:
            try:
                name = source()
                if name and len(name.strip()) > 2:
                    return name.strip()
            except:
                continue
        
        return None
    
    def extract_product_prices(self, link_element, page_soup):
        """Extract product prices from various sources"""
        prices = {
            'price_current': None,
            'price_original': None,
            'discount_percentage': None
        }
        
        # Look for prices in the link element and its parents
        search_elements = [link_element]
        
        # Add parent elements
        parent = link_element.parent
        for _ in range(3):
            if parent:
                search_elements.append(parent)
                parent = parent.parent
        
        price_values = []
        
        for element in search_elements:
            # Find price text patterns
            price_texts = element.find_all(text=re.compile(r'Rs\.\s*[\d,]+'))
            
            for price_text in price_texts:
                # Extract numerical value
                price_match = re.search(r'Rs\.\s*([\d,]+)', price_text)
                if price_match:
                    try:
                        price_value = float(price_match.group(1).replace(',', ''))
                        price_values.append(price_value)
                    except ValueError:
                        continue
        
        # Process found prices
        if price_values:
            unique_prices = list(set(price_values))
            unique_prices.sort()
            
            if len(unique_prices) == 1:
                prices['price_current'] = unique_prices[0]
            elif len(unique_prices) >= 2:
                prices['price_current'] = unique_prices[0]  # Lower price is current
                prices['price_original'] = unique_prices[-1]  # Higher price is original
                
                # Calculate discount percentage
                if prices['price_original'] > prices['price_current']:
                    discount = ((prices['price_original'] - prices['price_current']) / prices['price_original']) * 100
                    prices['discount_percentage'] = round(discount, 2)
        
        return prices
    
    def extract_product_image(self, link_element):
        """Extract product image URL"""
        img_tag = link_element.find('img')
        if img_tag:
            # Try different image source attributes
            src_attrs = ['src', 'data-src', 'data-lazy-src', 'data-original']
            
            for attr in src_attrs:
                src = img_tag.get(attr)
                if src:
                    # Clean and validate image URL
                    if src.startswith('data:'):  # Skip data URLs
                        continue
                    return urljoin(self.base_url, src)
        
        return None
    
    def extract_additional_product_info(self, link_element):
        """Extract additional product information"""
        info = {
            'in_stock': True,
            'prescription_required': False,
            'brand': None,
            'rating': None
        }
        
        # Get text content from element and parents
        text_content = link_element.get_text()
        parent = link_element.parent
        for _ in range(2):
            if parent:
                text_content += ' ' + parent.get_text()
                parent = parent.parent
        
        text_lower = text_content.lower()
        
        # Check stock status
        if any(keyword in text_lower for keyword in ['out of stock', 'not available', 'unavailable']):
            info['in_stock'] = False
        
        # Check prescription requirement
        if any(keyword in text_lower for keyword in ['prescription', 'rx required', 'doctor']):
            info['prescription_required'] = True
        
        # Try to extract brand (this is tricky without more specific structure)
        brand_patterns = [
            r'by\s+([A-Za-z\s]+)',
            r'brand:\s*([A-Za-z\s]+)',
            r'manufacturer:\s*([A-Za-z\s]+)'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                if len(brand) > 1 and not any(char.isdigit() for char in brand):
                    info['brand'] = brand
                    break
        
        return info
    
    def get_category_product_count(self, category_url):
        """Get the total number of products in a category"""
        soup = self.base_scraper.make_request(category_url)
        if not soup:
            return 0
        
        # Look for product count indicators
        count_selectors = [
            '.product-count',
            '.results-count',
            '[class*="count"]',
            '.total-products'
        ]
        
        for selector in count_selectors:
            count_elem = soup.select_one(selector)
            if count_elem:
                count_text = count_elem.get_text()
                # Extract number from text
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    return int(count_match.group(1))
        
        # Fallback: count product links on the page
        product_links = soup.select('a[href*="/p/"]')
        return len(product_links)


def test_advanced_scraper():
    """Test the advanced scraper functionality"""
    from dvago_scraper import DvagoScraper
    
    # Initialize base scraper
    base_scraper = DvagoScraper(output_dir="test_output", delay=1.0)
    
    # Initialize advanced scraper
    advanced_scraper = AdvancedDvagoScraper(base_scraper)
    
    # Test category discovery
    print("Testing category discovery...")
    categories = advanced_scraper.discover_all_categories()
    print(f"Found {len(categories)} categories")
    
    # Test product extraction from a category
    if categories:
        test_category = categories[0]
        print(f"\nTesting product extraction from: {test_category['name']}")
        products = advanced_scraper.extract_products_with_pagination(
            test_category['url'], 
            max_pages=2
        )
        print(f"Found {len(products)} products")
        
        # Print sample products
        for product in products[:3]:
            print(f"- {product['name']}: Rs. {product.get('price_current', 'N/A')}")


if __name__ == "__main__":
    test_advanced_scraper()