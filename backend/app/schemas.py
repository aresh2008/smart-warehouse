from pydantic import BaseModel,Field
from typing import Optional,List
class Login(BaseModel): email:str; password:str
class ProductIn(BaseModel):
 product_id:str; name:str; sku:str; category:str; supplier_id:int; warehouse_id:int; zone:str='A'; aisle:str='01'; rack:str='A1'; shelf:str='S1'; bin:str='B1'; current_stock:float=0; minimum_stock:float=10; maximum_capacity:float=100; reorder_level:float=20; unit:str='units'; unit_price:float=0; expiry_date:Optional[str]=None
class StockAdjust(BaseModel): quantity:float; note:str='Manual adjustment'
class ReceivingIn(BaseModel): invoice_number:str; vehicle:str; warehouse_id:int; tolerance:float=5; items:List[dict]
class DispatchIn(BaseModel): product_id:int; quantity:float; warehouse_id:int; destination:str; vehicle:str=''; customer_order:str=''; responsible:str='Manager'
class ChatIn(BaseModel): question:str
