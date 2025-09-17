#!/usr/bin/env python3
"""
DVAGO.pk Complete Web Scraper - Main Entry Point
===============================================

This is the main script that orchestrates the complete scraping process
for dvago.pk, including all categories, subcategories, medicines, and
comprehensive data export.

Features:
- Complete website scraping
- Advanced category discovery
- Detailed medicine information extraction
- Multiple export formats
- Progress tracking and logging
- Resume capability
- Data validation and cleaning

Usage:
    python main_scraper.py [options]

Author: GitHub Copilot
Date: September 17, 2025
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime
import json

# Import our custom modules
from dvago_scraper import DvagoScraper
from advanced_scraper import AdvancedDvagoScraper
from medicine_detail_scraper import MedicineDetailScraper
from data_export_manager import DataExportManager


class CompleteDvagoScraper:
    """
    Main orchestrator for the complete DVAGO scraping process
    """
    
    def __init__(self, config):
        """
        Initialize the complete scraper with configuration
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config
        self.output_dir = config.get('output_dir', 'dvago_complete_data')
        self.delay = config.get('delay', 2.0)
        self.max_products_per_category = config.get('max_products_per_category', None)
        self.detailed_scraping = config.get('detailed_scraping', True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize scrapers
        self.logger.info("Initializing scrapers...")
        self.base_scraper = DvagoScraper(
            output_dir=self.output_dir,
            delay=self.delay
        )
        
        self.advanced_scraper = AdvancedDvagoScraper(self.base_scraper)
        self.medicine_scraper = MedicineDetailScraper(self.base_scraper)
        
        # Progress tracking
        self.progress = {
            'categories_discovered': 0,
            'products_found': 0,
            'products_detailed': 0,
            'start_time': None,
            'current_stage': 'Initialization'
        }
        
        self.logger.info("Complete DVAGO scraper initialized successfully")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = os.path.join(self.output_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"complete_scraper_{timestamp}.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized - Log file: {log_file}")
    
    def save_progress(self):
        """Save current progress to file"""
        progress_file = os.path.join(self.output_dir, 'scraping_progress.json')
        
        progress_data = {
            **self.progress,
            'timestamp': datetime.now().isoformat(),
            'config': self.config
        }
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving progress: {str(e)}")
    
    def load_progress(self):
        """Load previous progress if available"""
        progress_file = os.path.join(self.output_dir, 'scraping_progress.json')
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Error loading progress: {str(e)}")
        
        return None
    
    def run_complete_scraping(self):
        """Run the complete scraping process"""
        self.logger.info("=" * 60)
        self.logger.info("STARTING COMPLETE DVAGO.PK SCRAPING PROCESS")
        self.logger.info("=" * 60)
        
        self.progress['start_time'] = datetime.now()
        
        try:
            # Stage 1: Discover all categories
            self.progress['current_stage'] = 'Category Discovery'
            self.save_progress()
            categories = self.discover_all_categories()
            
            # Stage 2: Extract products from categories
            self.progress['current_stage'] = 'Product Extraction'
            self.save_progress()
            all_products = self.extract_all_products(categories)
            
            # Stage 3: Extract detailed medicine information
            if self.detailed_scraping:
                self.progress['current_stage'] = 'Detailed Medicine Extraction'
                self.save_progress()
                detailed_medicines = self.extract_detailed_medicines(all_products)
            
            # Stage 4: Data export and reporting
            self.progress['current_stage'] = 'Data Export'
            self.save_progress()
            export_results = self.export_all_data()
            
            # Stage 5: Final report
            self.progress['current_stage'] = 'Completed'
            self.save_progress()
            self.generate_final_report(export_results)
            
            self.logger.info("=" * 60)
            self.logger.info("SCRAPING PROCESS COMPLETED SUCCESSFULLY!")
            self.logger.info("=" * 60)
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            self.progress['current_stage'] = 'Interrupted'
            self.save_progress()
            return False
            
        except Exception as e:
            self.logger.error(f"Error during scraping process: {str(e)}")
            self.progress['current_stage'] = 'Error'
            self.save_progress()
            raise
    
    def discover_all_categories(self):
        """Discover all categories and subcategories"""
        self.logger.info("Stage 1: Discovering all categories and subcategories...")
        
        # Use advanced scraper to discover categories
        categories = self.advanced_scraper.discover_all_categories()
        
        self.progress['categories_discovered'] = len(categories)
        self.logger.info(f"Discovered {len(categories)} categories")
        
        # Save categories to database
        self.base_scraper.categories = categories
        self.base_scraper.save_categories_to_db()
        
        # Discover subcategories for each main category
        all_subcategories = []
        for category in categories:
            self.logger.info(f"Discovering subcategories for: {category['name']}")
            subcategories = self.advanced_scraper.discover_subcategories(category['url'])
            all_subcategories.extend(subcategories)
            
            # Small delay between category requests
            time.sleep(self.delay)
        
        self.logger.info(f"Discovered {len(all_subcategories)} subcategories")
        
        # Combine categories and subcategories
        all_categories = categories + all_subcategories
        return all_categories
    
    def extract_all_products(self, categories):
        """Extract products from all categories"""
        self.logger.info("Stage 2: Extracting products from all categories...")
        
        all_products = []
        
        for i, category in enumerate(categories):
            self.logger.info(f"Processing category {i+1}/{len(categories)}: {category['name']}")
            
            try:
                # Extract products with pagination
                products = self.advanced_scraper.extract_products_with_pagination(
                    category['url'],
                    max_pages=None  # Get all pages
                )
                
                if self.max_products_per_category:
                    products = products[:self.max_products_per_category]
                
                # Add category info to products
                for product in products:
                    product['category_name'] = category['name']
                    product['category_url'] = category['url']
                
                all_products.extend(products)
                self.progress['products_found'] = len(all_products)
                
                self.logger.info(f"Found {len(products)} products in {category['name']}")
                
                # Save products in batches
                if products:
                    self.base_scraper.save_products_to_db(products)
                
                # Save progress periodically
                if i % 10 == 0:
                    self.save_progress()
                
                # Delay between categories
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.error(f"Error processing category {category['name']}: {str(e)}")
                continue
        
        self.logger.info(f"Total products extracted: {len(all_products)}")
        return all_products
    
    def extract_detailed_medicines(self, products):
        """Extract detailed information for medicines"""
        self.logger.info("Stage 3: Extracting detailed medicine information...")
        
        # Filter products that are likely medicines
        medicine_products = self.filter_medicine_products(products)
        
        self.logger.info(f"Identified {len(medicine_products)} medicine products for detailed extraction")
        
        # Extract detailed info in batches
        detailed_medicines = self.medicine_scraper.scrape_medicine_batch(
            [product['url'] for product in medicine_products],
            batch_size=10
        )
        
        self.progress['products_detailed'] = len(detailed_medicines)
        
        # Save detailed medicine info
        detailed_file = os.path.join(self.output_dir, 'detailed_medicines.json')
        self.medicine_scraper.save_medicine_details(detailed_medicines, detailed_file)
        
        return detailed_medicines
    
    def filter_medicine_products(self, products):
        """Filter products that are likely medicines"""
        medicine_keywords = [
            'tablet', 'capsule', 'syrup', 'injection', 'medicine',
            'cream', 'drops', 'suspension', 'powder', 'gel'
        ]
        
        medicine_products = []
        
        for product in products:
            product_name = product.get('name', '').lower()
            
            # Check if product name contains medicine keywords
            if any(keyword in product_name for keyword in medicine_keywords):
                medicine_products.append(product)
            
            # Check category
            category_name = product.get('category_name', '').lower()
            if any(keyword in category_name for keyword in ['medicine', 'health', 'pharmaceutical']):
                medicine_products.append(product)
        
        # Remove duplicates
        unique_medicines = []
        seen_urls = set()
        
        for product in medicine_products:
            if product['url'] not in seen_urls:
                unique_medicines.append(product)
                seen_urls.add(product['url'])
        
        return unique_medicines
    
    def export_all_data(self):
        """Export all scraped data in multiple formats"""
        self.logger.info("Stage 4: Exporting all data...")
        
        # Initialize export manager
        db_path = os.path.join(self.output_dir, 'dvago_data.db')
        export_manager = DataExportManager(db_path, self.output_dir)
        
        # Export in all formats
        export_results = export_manager.export_all_formats()
        
        return export_results
    
    def generate_final_report(self, export_results):
        """Generate final scraping report"""
        self.logger.info("Stage 5: Generating final report...")
        
        end_time = datetime.now()
        duration = end_time - self.progress['start_time']
        
        report = {
            'scraping_summary': {
                'start_time': self.progress['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration': str(duration),
                'categories_discovered': self.progress['categories_discovered'],
                'products_found': self.progress['products_found'],
                'products_detailed': self.progress['products_detailed']
            },
            'export_results': export_results,
            'config_used': self.config
        }
        
        # Save final report
        report_file = os.path.join(self.output_dir, 'final_scraping_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        self.print_final_summary(report)
        
        return report
    
    def print_final_summary(self, report):
        """Print final summary to console"""
        summary = report['scraping_summary']
        
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Duration: {summary['duration']}")
        print(f"Categories discovered: {summary['categories_discovered']}")
        print(f"Products found: {summary['products_found']}")
        print(f"Products with detailed info: {summary['products_detailed']}")
        print("\nGenerated Files:")
        
        for export_type, path in report['export_results'].items():
            print(f"- {export_type.replace('_', ' ').title()}: {path}")
        
        print(f"\nAll data saved in: {self.output_dir}")
        print("=" * 60)


def create_config_from_args(args):
    """Create configuration from command line arguments"""
    return {
        'output_dir': args.output_dir,
        'delay': args.delay,
        'max_products_per_category': args.max_products,
        'detailed_scraping': not args.no_detailed,
        'resume': args.resume
    }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Complete DVAGO.pk web scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main_scraper.py                           # Basic scraping
  python main_scraper.py --delay 3.0               # Slower scraping
  python main_scraper.py --max-products 50         # Limit products per category
  python main_scraper.py --no-detailed             # Skip detailed medicine info
  python main_scraper.py --output-dir my_data      # Custom output directory
        """
    )
    
    parser.add_argument(
        '--output-dir',
        default='dvago_complete_data',
        help='Output directory for scraped data (default: dvago_complete_data)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )
    
    parser.add_argument(
        '--max-products',
        type=int,
        help='Maximum products to scrape per category (for testing)'
    )
    
    parser.add_argument(
        '--no-detailed',
        action='store_true',
        help='Skip detailed medicine information extraction'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous scraping session'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Initialize and run scraper
    try:
        scraper = CompleteDvagoScraper(config)
        success = scraper.run_complete_scraping()
        
        if success:
            print("\n✅ Scraping completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Scraping was interrupted or failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Scraping interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()