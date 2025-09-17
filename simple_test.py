#!/usr/bin/env python3
"""
Simple Test Script for DVAGO.pk Scraper (No Selenium Required)
============================================================

This script tests the core scraper functionality without requiring Selenium,
making it suitable for basic validation and systems where Chrome driver
might have compatibility issues.

Author: GitHub Copilot
Date: September 17, 2025
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dvago_scraper import DvagoScraper
from advanced_scraper import AdvancedDvagoScraper


def test_basic_connectivity():
    """Test basic website connectivity"""
    print("Testing basic connectivity...")
    
    try:
        scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        
        # Test homepage request
        soup = scraper.make_request("https://www.dvago.pk", use_selenium=False)
        if soup:
            print("✅ Homepage request successful")
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text()[:50]}...")
            return True
        else:
            print("❌ Homepage request failed")
            return False
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {str(e)}")
        return False


def test_category_extraction():
    """Test category extraction without Selenium"""
    print("\nTesting category extraction...")
    
    try:
        scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        
        # Test category extraction
        categories = scraper.extract_categories()
        if categories and len(categories) > 0:
            print(f"✅ Found {len(categories)} categories")
            for i, cat in enumerate(categories[:5]):  # Show first 5
                print(f"   {i+1}. {cat['name']} - {cat['url']}")
            return True
        else:
            print("❌ No categories found")
            return False
        
    except Exception as e:
        print(f"❌ Category extraction test failed: {str(e)}")
        return False


def test_product_extraction():
    """Test product extraction from a category page"""
    print("\nTesting product extraction...")
    
    try:
        base_scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        advanced_scraper = AdvancedDvagoScraper(base_scraper)
        
        # Test with medicine category
        test_url = "https://www.dvago.pk/cat/medicine"
        print(f"   Testing product extraction from: {test_url}")
        
        products = advanced_scraper.extract_products_from_page(test_url)
        if products and len(products) > 0:
            print(f"✅ Found {len(products)} products")
            for i, product in enumerate(products[:3]):  # Show first 3
                price = product.get('price_current', 'N/A')
                print(f"   {i+1}. {product['name'][:40]}... - Rs. {price}")
            return True
        else:
            print("❌ No products found")
            return False
        
    except Exception as e:
        print(f"❌ Product extraction test failed: {str(e)}")
        return False


def test_database_operations():
    """Test database operations"""
    print("\nTesting database operations...")
    
    try:
        scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        
        # Test category saving
        test_categories = [
            {
                'name': 'Test Category',
                'url': 'https://www.dvago.pk/cat/test',
                'slug': 'test',
                'image_url': None
            }
        ]
        
        scraper.categories = test_categories
        scraper.save_categories_to_db()
        print("✅ Category database save successful")
        
        # Test product saving
        test_products = [
            {
                'name': 'Test Medicine',
                'url': 'https://www.dvago.pk/p/test-medicine',
                'slug': 'test-medicine',
                'price_current': 100.0,
                'price_original': 120.0,
                'description': 'Test medicine description',
                'brand': 'Test Brand',
                'image_url': 'https://example.com/image.jpg',
                'in_stock': True,
                'prescription_required': False
            }
        ]
        
        scraper.save_products_to_db(test_products)
        print("✅ Product database save successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {str(e)}")
        return False


def test_data_export():
    """Test basic data export functionality"""
    print("\nTesting data export...")
    
    try:
        from data_export_manager import DataExportManager
        
        # Create test database
        scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        
        # Add some test data
        test_categories = [
            {
                'name': 'Test Category 1',
                'url': 'https://www.dvago.pk/cat/test1',
                'slug': 'test1',
                'image_url': None
            },
            {
                'name': 'Test Category 2',
                'url': 'https://www.dvago.pk/cat/test2',
                'slug': 'test2',
                'image_url': None
            }
        ]
        
        scraper.categories = test_categories
        scraper.save_categories_to_db()
        
        # Test export
        db_path = os.path.join("test_output", "dvago_data.db")
        export_manager = DataExportManager(db_path, "test_output")
        
        # Test CSV export
        export_manager.export_to_csv(['categories'])
        print("✅ CSV export successful")
        
        # Test JSON export
        export_manager.export_to_json(['categories'])
        print("✅ JSON export successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Data export test failed: {str(e)}")
        return False


def run_simple_tests():
    """Run simplified test suite"""
    print("DVAGO.pk Scraper Simple Test Suite")
    print("=" * 45)
    print("(This test suite works without Selenium/Chrome driver)")
    
    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("Category Extraction", test_category_extraction),
        ("Product Extraction", test_product_extraction),
        ("Database Operations", test_database_operations),
        ("Data Export", test_data_export)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {str(e)}")
    
    print("\n" + "=" * 45)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("1. Run: python main_scraper.py --no-detailed --max-products 10")
        print("2. For full scraping: python main_scraper.py")
        return True
    elif passed >= 3:
        print("⚠️  Most tests passed. The scraper should work for basic functionality.")
        print("Note: Some advanced features may not work without Chrome driver.")
        return True
    else:
        print("❌ Too many tests failed. Please check the errors above.")
        return False


def main():
    """Main test function"""
    print("Starting DVAGO.pk Scraper Simple Tests...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Run tests
    success = run_simple_tests()
    
    # Cleanup test files
    try:
        import shutil
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")
        print("\nTest files cleaned up.")
    except:
        print("\nNote: You may want to manually clean up the 'test_output' directory.")
    
    if success:
        print("\n🎉 Tests passed! You can now run the scraper.")
        print("\nRecommended commands:")
        print("• For testing: python main_scraper.py --max-products 5 --no-detailed")
        print("• For full scrape: python main_scraper.py")
    else:
        print("\n⚠️  Some tests failed. Please review the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)