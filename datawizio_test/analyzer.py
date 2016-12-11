from __future__ import division
import datetime
import requests_cache
import math

from dwapi import datawiz

class Struct:

    def __init__(self):
        self.products = {}
        self.qty = 0
        self.sum = 0
        self.products_count = 0
        self.receipt = 0

class Analyzer(object):

    def __new__(cls, *args, **kwargs):
        try:
            dw = datawiz.DW(kwargs.get("login", ""), kwargs.get("password", ""))
            dw.get_client_info()
            return super(Analyzer, cls).__new__(cls)
        except:
            return None

    def __init__(self, login="", password="", date_first=datetime.datetime(2015, 11, 18), date_second=datetime.datetime(2015, 11, 17)):
        self.products_one = Struct()
        self.products_two = Struct()
        self.product_set = set()
        self.up_list = []
        self.low_list = []
        requests_cache.install_cache('test_cache', backend='redis', expire_after=600)
        self.dw = datawiz.DW(login, password)
        self.client_info = self.dw.get_client_info()
        self.get_recipts(self.products_one, date_first)
        self.get_recipts(self.products_two, date_second)
        self.calc_products()

    def get_recipts(self, products_struct, date):
        all_recipts = self.dw.get_receipts(date_from=date, date_to=date, type="full")
        products_struct.qty = len(all_recipts)
        for item in all_recipts:
            for product in item.get("cartitems"):
                self.product_set.add(product.get("product__name"))
                products_struct.products.setdefault(product.get("product__name"), {"qty": 0, "total_price": 0})
                products_struct.products[product.get("product__name")]["qty"] += product.get("qty")
                products_struct.products_count += product.get("qty")
                products_struct.products[product.get("product__name")]["total_price"] += product.get("total_price")

            products_struct.sum += item.get("turnover")
        products_struct.receipt = products_struct.sum / products_struct.qty if products_struct != 0 else 0

    def calc_products(self):
        product_list = list(self.product_set)
        product_list.sort()
        for product in product_list:
            qty = self.products_one.products.get(product, {}).get("qty", 0.0) - self.products_two.products.get(product, {}).get("qty", 0.0)
            total_price = self.products_one.products.get(product, {}).get("total_price", 0.0) - self.products_two.products.get(product, {}).get("total_price", 0.0)
            if qty < 0:
                self.low_list.append([product, qty, total_price])
            elif qty > 0:
                self.up_list.append([product, qty, total_price])

    def update(self, who, date):
        self.product_set.clear()
        self.up_list[:] = []
        self.low_list[:] = []
        if date > self.client_info.get("date_to") or date <self.client_info.get("date_from"):
            print("Wrong date")
            return False
        if who == "one":
            self.products_one = Struct()
            self.product_set.update(self.products_two.products.keys())
            self.get_recipts(self.products_one, date)
        elif who == "two":
            self.products_two = Struct()
            self.product_set.update(self.products_one.products.keys())
            self.get_recipts(self.products_two, date)
        else:
            print("Bad request")
            return False
        self.calc_products()
        return True

    def get_client_info(self):
        result = {}
        result["name"] = self.client_info.get("name")
        result["date_from"] = str(self.client_info.get("date_from"))
        result["date_to"] = str(self.client_info.get("date_to"))
        result["shops"] = self.dw.get_shops().values
        return result

    def dif_in_prc(self, one, two):
        if one == 0:
            return 0
        else:
            return (one - two) * 100 / one

    def get_main_table(self):
        row1 = []
        row1.append(self.products_one.sum)
        row1.append(self.products_two.sum)
        row1.append(self.dif_in_prc(self.products_one.sum, self.products_two.sum))
        row1.append(self.products_one.sum - self.products_two.sum)
        row2 = []
        row2.append(self.products_one.products_count)
        row2.append(self.products_two.products_count)
        row2.append(self.dif_in_prc(self.products_one.products_count, self.products_two.products_count))
        row2.append(self.products_one.products_count - self.products_two.products_count)
        row3 = []
        row3.append(self.products_one.qty)
        row3.append(self.products_two.qty)
        row3.append(self.dif_in_prc(self.products_one.qty, self.products_two.qty))
        row3.append(self.products_one.qty - self.products_two.qty)
        row4 = []
        row4.append(self.products_one.receipt)
        row4.append(self.products_two.receipt)
        row4.append(self.dif_in_prc(self.products_one.receipt, self.products_two.receipt))
        row4.append(self.products_one.receipt - self.products_two.receipt)
        result = [row1, row2, row3, row4]
        return result

    def get_other_tables(self, page):
        low = []
        up = []
        for i in range(page*50 - 50, page*50):
            try:
                low.append(self.low_list[i])
            except:
                pass
            try:
                up.append(self.up_list[i])
            except:
                pass
        return (up, low)

    def get_pages_count(self):
        low_pgs = math.ceil(len(self.low_list) / 50)
        up_pgs = math.ceil(len(self.up_list) / 50)
        return max(low_pgs, up_pgs)
