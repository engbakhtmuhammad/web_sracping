#!/usr/bin/env python3
"""
Test Script for DVAGO.pk Scraper
===============================

This script runs basic tests to validate the scraper functionality
without performing a full scrape.

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
from medicine_detail_scraper import MedicineDetailScraper


def test_basic_scraper():
    """Test basic scraper functionality"""
    print("Testing basic scraper...")
    
    try:
        scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        
        # Test homepage request
        soup = scraper.make_request("https://www.dvago.pk")
        if soup:
            print("✅ Homepage request successful")
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text()[:50]}...")
        else:
            print("❌ Homepage request failed")
            return False
        
        # Test category extraction
        categories = scraper.extract_categories()
        if categories:
            print(f"✅ Found {len(categories)} categories")
            for i, cat in enumerate(categories[:3]):
                print(f"   {i+1}. {cat['name']} - {cat['url']}")
        else:
            print("❌ No categories found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic scraper test failed: {str(e)}")
        return False


def test_advanced_scraper():
    """Test advanced scraper functionality"""
    print("\nTesting advanced scraper...")
    
    try:
        base_scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        advanced_scraper = AdvancedDvagoScraper(base_scraper)
        
        # Test category discovery
        categories = advanced_scraper.discover_all_categories()
        if categories:
            print(f"✅ Advanced category discovery found {len(categories)} categories")
        else:
            print("❌ Advanced category discovery failed")
            return False
        
        # Test product extraction from first category
        if categories:
            test_category = categories[0]
            print(f"   Testing product extraction from: {test_category['name']}")
            
            products = advanced_scraper.extract_products_from_page(test_category['url'])
            if products:
                print(f"✅ Found {len(products)} products")
                for i, product in enumerate(products[:3]):
                    price = product.get('price_current', 'N/A')
                    print(f"   {i+1}. {product['name'][:40]}... - Rs. {price}")
            else:
                print("❌ No products found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced scraper test failed: {str(e)}")
        return False


def test_medicine_scraper():
    """Test medicine detail scraper"""
    print("\nTesting medicine detail scraper...")
    
    try:
        base_scraper = DvagoScraper(output_dir="test_output", delay=1.0)
        medicine_scraper = MedicineDetailScraper(base_scraper)
        
        # Test with a known medicine URL (you might need to update this)
        test_url = "https://www.dvago.pk/p/panadol-500mg-tablets"
        
        print(f"   Testing detailed extraction from: {test_url}")
        medicine_info = medicine_scraper.extract_complete_medicine_info(test_url)
        
        if medicine_info:
            print("✅ Medicine detail extraction successful")
            print(f"   Name: {medicine_info.get('name', 'N/A')}")
            print(f"   Price: Rs. {medicine_info.get('price_current', 'N/A')}")
            print(f"   Manufacturer: {medicine_info.get('manufacturer', 'N/A')}")
            print(f"   Images found: {len(medicine_info.get('images', []))}")
        else:
            print("❌ Medicine detail extraction failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Medicine scraper test failed: {str(e)}")
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


def run_all_tests():
    """Run all tests"""
    print("DVAGO.pk Scraper Test Suite")
    print("=" * 40)
    
    tests = [
        ("Basic Scraper", test_basic_scraper),
        ("Advanced Scraper", test_advanced_scraper),
        ("Medicine Scraper", test_medicine_scraper),
        ("Database Operations", test_database_operations)
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
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! The scraper is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False


def main():
    """Main test function"""
    print("Starting DVAGO.pk Scraper Tests...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test output directory
    os.makedirs("test_output", exist_ok=True)
    
    # Run tests
    success = run_all_tests()
    
    # Cleanup test files
    try:
        import shutil
        if os.path.exists("test_output"):
            shutil.rmtree("test_output")
        print("\nTest files cleaned up.")
    except:
        print("\nNote: You may want to manually clean up the 'test_output' directory.")
    
    if success:
        print("\n🎉 All tests passed! You can now run the main scraper.")
        print("Usage: python main_scraper.py")
    else:
        print("\n⚠️  Some tests failed. Please review the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)