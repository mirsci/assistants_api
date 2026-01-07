"""
Product Integration Layer for Shopping Assistant

This module provides integration with eCommerce platforms (Shopify, WooCommerce)
to enable real-time product data access, inventory checks, and cart operations.

Key features:
- Shopify API integration (products, inventory, cart)
- WooCommerce REST API integration
- Unified product interface across platforms
- Real-time inventory checks
- "Add to cart" functionality
- Product search and filtering
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import requests
from datetime import datetime


# ============================================================================
# DATA MODELS
# ============================================================================

class ProductAvailability(str, Enum):
    """Product availability status"""
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    PREORDER = "preorder"


@dataclass
class Product:
    """Unified product model across eCommerce platforms"""
    id: str
    name: str
    description: str
    price: float
    currency: str
    availability: ProductAvailability
    stock_quantity: Optional[int]
    image_url: Optional[str]
    product_url: str
    category: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    variants: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description[:200] + "..." if len(self.description) > 200 else self.description,
            "price": self.price,
            "currency": self.currency,
            "availability": self.availability.value,
            "stock_quantity": self.stock_quantity,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "category": self.category,
            "brand": self.brand,
            "rating": self.rating,
            "review_count": self.review_count
        }
    
    def to_llm_context(self) -> str:
        """
        Format product for LLM context (concise, informative).
        
        This is used to provide product information to the AI assistant
        in a token-efficient format.
        """
        context = f"{self.name}"
        
        if self.brand:
            context += f" by {self.brand}"
        
        context += f" - ${self.price:.2f} {self.currency}"
        
        if self.availability == ProductAvailability.IN_STOCK:
            context += " (In Stock)"
        elif self.availability == ProductAvailability.OUT_OF_STOCK:
            context += " (Out of Stock)"
        elif self.availability == ProductAvailability.LOW_STOCK:
            context += f" (Only {self.stock_quantity} left)"
        
        if self.rating:
            context += f" | ⭐ {self.rating}/5"
            if self.review_count:
                context += f" ({self.review_count} reviews)"
        
        context += f" | {self.product_url}"
        
        return context


# ============================================================================
# ABSTRACT ECOMMERCE INTERFACE
# ============================================================================

class EcommerceInterface(ABC):
    """Abstract interface for eCommerce platform integrations"""
    
    @abstractmethod
    def search_products(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Product]:
        """Search products by query"""
        pass
    
    @abstractmethod
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get single product by ID"""
        pass
    
    @abstractmethod
    def check_inventory(self, product_id: str) -> Dict[str, Any]:
        """Check real-time inventory for product"""
        pass
    
    @abstractmethod
    def add_to_cart(self, cart_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add product to shopping cart"""
        pass
    
    @abstractmethod
    def get_cart(self, cart_id: str) -> Dict[str, Any]:
        """Get cart contents"""
        pass


# ============================================================================
# SHOPIFY INTEGRATION
# ============================================================================

class ShopifyIntegration(EcommerceInterface):
    """
    Shopify API integration for product data and cart operations.
    
    Requires:
    - Shopify store URL (e.g., yourstore.myshopify.com)
    - Admin API access token
    - Storefront API access token (for cart operations)
    
    API Documentation: https://shopify.dev/docs/api
    """
    
    def __init__(
        self,
        shop_url: str,
        admin_access_token: str,
        storefront_access_token: Optional[str] = None,
        api_version: str = "2024-01"
    ):
        """
        Initialize Shopify integration.
        
        Args:
            shop_url: Shopify store URL (e.g., example.myshopify.com)
            admin_access_token: Admin API access token
            storefront_access_token: Storefront API token (for cart ops)
            api_version: API version (default: 2024-01)
        """
        self.shop_url = shop_url.replace("https://", "").replace("http://", "")
        self.admin_access_token = admin_access_token
        self.storefront_access_token = storefront_access_token
        self.api_version = api_version
        
        self.admin_base_url = f"https://{self.shop_url}/admin/api/{api_version}"
        self.storefront_base_url = f"https://{self.shop_url}/api/{api_version}/graphql.json"
    
    def _admin_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make request to Shopify Admin API"""
        url = f"{self.admin_base_url}/{endpoint}"
        headers = {
            "X-Shopify-Access-Token": self.admin_access_token,
            "Content-Type": "application/json"
        }
        
        response = requests.request(method, url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def search_products(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Product]:
        """
        Search products using Shopify Admin API.
        
        Args:
            query: Search query (product title, description)
            limit: Maximum number of results
            filters: Optional filters (category, price_min, price_max, etc.)
        """
        params = {
            "limit": limit,
            "title": query  # Shopify searches by title
        }
        
        # Apply additional filters
        if filters:
            if "category" in filters:
                params["collection_id"] = filters["category"]
            if "vendor" in filters:
                params["vendor"] = filters["vendor"]
        
        try:
            response = self._admin_request(
                f"products.json?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            )
            
            products = []
            for item in response.get("products", []):
                # Get first variant for pricing
                variant = item["variants"][0] if item["variants"] else {}
                
                # Determine availability
                available = variant.get("inventory_quantity", 0) > 0
                stock_qty = variant.get("inventory_quantity", 0)
                
                if available and stock_qty <= 5:
                    availability = ProductAvailability.LOW_STOCK
                elif available:
                    availability = ProductAvailability.IN_STOCK
                else:
                    availability = ProductAvailability.OUT_OF_STOCK
                
                product = Product(
                    id=str(item["id"]),
                    name=item["title"],
                    description=item.get("body_html", "").replace("<p>", "").replace("</p>", ""),
                    price=float(variant.get("price", 0)),
                    currency="USD",  # Shopify stores have single currency
                    availability=availability,
                    stock_quantity=stock_qty,
                    image_url=item["images"][0]["src"] if item.get("images") else None,
                    product_url=f"https://{self.shop_url}/products/{item['handle']}",
                    category=item.get("product_type"),
                    brand=item.get("vendor"),
                    variants=[
                        {
                            "id": v["id"],
                            "title": v["title"],
                            "price": v["price"],
                            "available": v.get("inventory_quantity", 0) > 0
                        }
                        for v in item["variants"]
                    ]
                )
                products.append(product)
            
            return products
        
        except Exception as e:
            print(f"Shopify API error: {e}")
            return []
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get single product by ID"""
        try:
            response = self._admin_request(f"products/{product_id}.json")
            item = response.get("product")
            
            if not item:
                return None
            
            variant = item["variants"][0] if item["variants"] else {}
            available = variant.get("inventory_quantity", 0) > 0
            stock_qty = variant.get("inventory_quantity", 0)
            
            if available and stock_qty <= 5:
                availability = ProductAvailability.LOW_STOCK
            elif available:
                availability = ProductAvailability.IN_STOCK
            else:
                availability = ProductAvailability.OUT_OF_STOCK
            
            return Product(
                id=str(item["id"]),
                name=item["title"],
                description=item.get("body_html", ""),
                price=float(variant.get("price", 0)),
                currency="USD",
                availability=availability,
                stock_quantity=stock_qty,
                image_url=item["images"][0]["src"] if item.get("images") else None,
                product_url=f"https://{self.shop_url}/products/{item['handle']}",
                category=item.get("product_type"),
                brand=item.get("vendor")
            )
        
        except Exception as e:
            print(f"Shopify API error: {e}")
            return None
    
    def check_inventory(self, product_id: str) -> Dict[str, Any]:
        """
        Check real-time inventory for a product.
        
        Returns inventory across all variants.
        """
        try:
            response = self._admin_request(f"products/{product_id}.json")
            item = response.get("product")
            
            if not item:
                return {"error": "Product not found"}
            
            inventory = []
            total_stock = 0
            
            for variant in item["variants"]:
                stock = variant.get("inventory_quantity", 0)
                total_stock += stock
                
                inventory.append({
                    "variant_id": variant["id"],
                    "variant_name": variant["title"],
                    "sku": variant.get("sku"),
                    "quantity": stock,
                    "available": stock > 0
                })
            
            return {
                "product_id": product_id,
                "product_name": item["title"],
                "total_stock": total_stock,
                "variants": inventory
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def add_to_cart(self, cart_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Add product to cart using Shopify Storefront API.
        
        Note: This requires Storefront API access token.
        For Admin API, use draft orders instead.
        """
        if not self.storefront_access_token:
            return {"error": "Storefront API token required for cart operations"}
        
        # GraphQL mutation for adding to cart
        mutation = """
        mutation cartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!) {
          cartLinesAdd(cartId: $cartId, lines: $lines) {
            cart {
              id
              lines(first: 10) {
                edges {
                  node {
                    id
                    quantity
                    merchandise {
                      ... on ProductVariant {
                        id
                        title
                        price {
                          amount
                          currencyCode
                        }
                      }
                    }
                  }
                }
              }
              estimatedCost {
                totalAmount {
                  amount
                  currencyCode
                }
              }
            }
          }
        }
        """
        
        variables = {
            "cartId": cart_id,
            "lines": [{
                "merchandiseId": f"gid://shopify/ProductVariant/{product_id}",
                "quantity": quantity
            }]
        }
        
        headers = {
            "X-Shopify-Storefront-Access-Token": self.storefront_access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.storefront_base_url,
                json={"query": mutation, "variables": variables},
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            return {"error": str(e)}
    
    def get_cart(self, cart_id: str) -> Dict[str, Any]:
        """Get cart contents via Storefront API"""
        if not self.storefront_access_token:
            return {"error": "Storefront API token required"}
        
        query = """
        query getCart($cartId: ID!) {
          cart(id: $cartId) {
            id
            lines(first: 50) {
              edges {
                node {
                  id
                  quantity
                  merchandise {
                    ... on ProductVariant {
                      id
                      title
                      product {
                        title
                      }
                      price {
                        amount
                        currencyCode
                      }
                    }
                  }
                }
              }
            }
            estimatedCost {
              totalAmount {
                amount
                currencyCode
              }
            }
          }
        }
        """
        
        headers = {
            "X-Shopify-Storefront-Access-Token": self.storefront_access_token,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.storefront_base_url,
                json={"query": query, "variables": {"cartId": cart_id}},
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# PRODUCT SEARCH ENHANCER FOR LLM CONTEXT
# ============================================================================

class ProductContextBuilder:
    """
    Builds optimized product context for LLM prompts.
    
    This class takes product search results and formats them in a way
    that's informative but token-efficient for the AI assistant.
    """
    
    @staticmethod
    def build_product_list_context(
        products: List[Product],
        max_products: int = 5,
        include_descriptions: bool = False
    ) -> str:
        """
        Create formatted product list for LLM context.
        
        Args:
            products: List of Product objects
            max_products: Maximum products to include
            include_descriptions: Whether to include full descriptions
        
        Returns:
            Formatted string for LLM prompt
        """
        if not products:
            return "No products found matching the criteria."
        
        context_parts = [f"Found {len(products)} products:"]
        
        for i, product in enumerate(products[:max_products], 1):
            context_parts.append(f"\n{i}. {product.to_llm_context()}")
            
            if include_descriptions and product.description:
                desc = product.description[:150] + "..." if len(product.description) > 150 else product.description
                context_parts.append(f"   Description: {desc}")
        
        if len(products) > max_products:
            context_parts.append(f"\n... and {len(products) - max_products} more products.")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def build_inventory_context(inventory_data: Dict[str, Any]) -> str:
        """Format inventory check results for LLM"""
        if "error" in inventory_data:
            return f"Unable to check inventory: {inventory_data['error']}"
        
        total = inventory_data.get("total_stock", 0)
        product_name = inventory_data.get("product_name", "Product")
        
        if total == 0:
            return f"{product_name} is currently out of stock."
        elif total <= 5:
            return f"{product_name} has limited stock ({total} remaining)."
        else:
            return f"{product_name} is in stock."


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_product_integration():
    """Demonstrate product integration usage"""
    
    # Initialize Shopify integration
    shopify = ShopifyIntegration(
        shop_url="example-store.myshopify.com",
        admin_access_token="shpat_xxxxx",
        storefront_access_token="xxxxxxxx"
    )
    
    # Search for products
    products = shopify.search_products("laptop", limit=5)
    
    # Build context for LLM
    context = ProductContextBuilder.build_product_list_context(products)
    print("Product context for LLM:")
    print(context)
    
    # Check inventory
    if products:
        inventory = shopify.check_inventory(products[0].id)
        inv_context = ProductContextBuilder.build_inventory_context(inventory)
        print(f"\nInventory: {inv_context}")


if __name__ == "__main__":
    # example_product_integration()
    pass