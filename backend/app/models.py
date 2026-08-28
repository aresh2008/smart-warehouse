from sqlalchemy import Column,Integer,String,Float,DateTime,Boolean,ForeignKey,Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
class Stamp:
 created_at=Column(DateTime,server_default=func.now()); updated_at=Column(DateTime,server_default=func.now(),onupdate=func.now())
class Role(Base,Stamp):
 __tablename__='roles'; id=Column(Integer,primary_key=True); name=Column(String,unique=True,index=True)
class User(Base,Stamp):
 __tablename__='users'; id=Column(Integer,primary_key=True); name=Column(String); email=Column(String,unique=True,index=True); password_hash=Column(String); role_id=Column(Integer,ForeignKey('roles.id')); role=relationship('Role')
class Warehouse(Base,Stamp):
 __tablename__='warehouses'; id=Column(Integer,primary_key=True); name=Column(String,index=True); location=Column(String); capacity=Column(Float,default=10000)
class Zone(Base,Stamp):
 __tablename__='zones'; id=Column(Integer,primary_key=True); name=Column(String); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); capacity=Column(Float,default=2000); warehouse=relationship('Warehouse')
class Rack(Base,Stamp):
 __tablename__='racks'; id=Column(Integer,primary_key=True); code=Column(String,index=True); zone_id=Column(Integer,ForeignKey('zones.id')); zone=relationship('Zone')
class Shelf(Base,Stamp):
 __tablename__='shelves'; id=Column(Integer,primary_key=True); code=Column(String); rack_id=Column(Integer,ForeignKey('racks.id'))
class Supplier(Base,Stamp):
 __tablename__='suppliers'; id=Column(Integer,primary_key=True); name=Column(String); contact=Column(String)
class Product(Base,Stamp):
 __tablename__='products'; id=Column(Integer,primary_key=True); product_id=Column(String,unique=True,index=True); name=Column(String,index=True); sku=Column(String,unique=True,index=True); category=Column(String,index=True); supplier_id=Column(Integer,ForeignKey('suppliers.id')); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); zone=Column(String); aisle=Column(String); rack=Column(String); shelf=Column(String); bin=Column(String); current_stock=Column(Float,default=0); minimum_stock=Column(Float); maximum_capacity=Column(Float); reorder_level=Column(Float); unit=Column(String); unit_price=Column(Float); expiry_date=Column(String,nullable=True); supplier=relationship('Supplier'); warehouse=relationship('Warehouse')
class Inventory(Base,Stamp):
 __tablename__='inventory'; id=Column(Integer,primary_key=True); product_id=Column(Integer,ForeignKey('products.id'),index=True); quantity=Column(Float); product=relationship('Product')
class InventoryTransaction(Base,Stamp):
 __tablename__='inventory_transactions'; id=Column(Integer,primary_key=True); product_id=Column(Integer,ForeignKey('products.id'),index=True); transaction_type=Column(String); quantity=Column(Float); reference=Column(String); note=Column(Text); product=relationship('Product')
class Invoice(Base,Stamp):
 __tablename__='invoices'; id=Column(Integer,primary_key=True); number=Column(String,unique=True); supplier_id=Column(Integer,ForeignKey('suppliers.id'))
class Receiving(Base,Stamp):
 __tablename__='receivings'; id=Column(Integer,primary_key=True); invoice_number=Column(String,index=True); vehicle=Column(String); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); status=Column(String,default='PENDING'); tolerance=Column(Float,default=5); verified_at=Column(DateTime,nullable=True); warehouse=relationship('Warehouse'); items=relationship('ReceivingItem',cascade='all,delete-orphan')
class ReceivingItem(Base,Stamp):
 __tablename__='receiving_items'; id=Column(Integer,primary_key=True); receiving_id=Column(Integer,ForeignKey('receivings.id')); product_id=Column(Integer,ForeignKey('products.id')); expected_qty=Column(Float); detected_qty=Column(Float,nullable=True); confidence=Column(Float,nullable=True); expected_weight=Column(Float,nullable=True); actual_weight=Column(Float,nullable=True); product=relationship('Product')
class StockDispatch(Base,Stamp):
 __tablename__='dispatches'; id=Column(Integer,primary_key=True); product_id=Column(Integer,ForeignKey('products.id')); quantity=Column(Float); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); destination=Column(String); vehicle=Column(String); customer_order=Column(String); responsible=Column(String); status=Column(String,default='APPROVED'); product=relationship('Product')
class Worker(Base,Stamp):
 __tablename__='workers'; id=Column(Integer,primary_key=True); worker_id=Column(String,unique=True); name=Column(String); department=Column(String); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); shift=Column(String); warehouse=relationship('Warehouse')
class Attendance(Base,Stamp):
 __tablename__='attendance'; id=Column(Integer,primary_key=True); worker_id=Column(Integer,ForeignKey('workers.id')); entry_time=Column(DateTime,nullable=True); exit_time=Column(DateTime,nullable=True); status=Column(String); activity=Column(String); ppe_compliance=Column(String); worker=relationship('Worker')
class Camera(Base,Stamp):
 __tablename__='cameras'; id=Column(Integer,primary_key=True); camera_id=Column(String,unique=True); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); zone=Column(String); status=Column(String,default='ONLINE')
class SafetyEvent(Base,Stamp):
 __tablename__='safety_events'; id=Column(Integer,primary_key=True); worker_id=Column(Integer,ForeignKey('workers.id')); camera_id=Column(Integer,ForeignKey('cameras.id')); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); zone=Column(String); helmet=Column(Boolean); gloves=Column(Boolean); ppe_status=Column(String); violation_type=Column(String,nullable=True); confidence=Column(Float); event_status=Column(String,default='OPEN'); worker=relationship('Worker'); camera=relationship('Camera')
class Vehicle(Base,Stamp):
 __tablename__='vehicles'; id=Column(Integer,primary_key=True); vehicle_id=Column(String,unique=True); location=Column(String); zone=Column(String); speed=Column(Float); battery=Column(Float); temperature=Column(Float); engine_status=Column(String); health_score=Column(Float); maintenance_status=Column(String); operating_hours=Column(Float,default=0)
class VehicleSensor(Base,Stamp):
 __tablename__='vehicle_sensors'; id=Column(Integer,primary_key=True); vehicle_id=Column(Integer,ForeignKey('vehicles.id')); speed=Column(Float); temperature=Column(Float); battery=Column(Float); vibration=Column(Float); operating_hours=Column(Float)
class VehicleHealth(Base,Stamp):
 __tablename__='vehicle_health'; id=Column(Integer,primary_key=True); vehicle_id=Column(Integer,ForeignKey('vehicles.id')); score=Column(Float); recommendation=Column(String)
class MaintenanceTask(Base,Stamp):
 __tablename__='maintenance_tasks'; id=Column(Integer,primary_key=True); title=Column(String); asset_type=Column(String); asset_id=Column(String); due_date=Column(String); status=Column(String); priority=Column(String)
class EnergyReading(Base,Stamp):
 __tablename__='energy_readings'; id=Column(Integer,primary_key=True); warehouse_id=Column(Integer,ForeignKey('warehouses.id')); zone=Column(String); power_kw=Column(Float); consumed_kwh=Column(Float); reading_date=Column(String,index=True)
class EnergyCost(Base,Stamp):
 __tablename__='energy_costs'; id=Column(Integer,primary_key=True); tariff=Column(Float,default=8.5); monthly_cost=Column(Float)
class AIInsight(Base,Stamp):
 __tablename__='ai_insights'; id=Column(Integer,primary_key=True); severity=Column(String); title=Column(String); description=Column(Text); module=Column(String); location=Column(String); action_url=Column(String); status=Column(String,default='OPEN')
class ChatHistory(Base,Stamp):
 __tablename__='chat_history'; id=Column(Integer,primary_key=True); user_id=Column(Integer,ForeignKey('users.id')); question=Column(Text); answer=Column(Text)
class Report(Base,Stamp):
 __tablename__='reports'; id=Column(Integer,primary_key=True); name=Column(String); report_type=Column(String); generated_by=Column(Integer,ForeignKey('users.id'))
class Notification(Base,Stamp):
 __tablename__='notifications'; id=Column(Integer,primary_key=True); title=Column(String); message=Column(Text); severity=Column(String); read=Column(Boolean,default=False)
