import sys,random
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from app.database import Base,engine,SessionLocal
from app.models import *
from app.auth import hash_password
from datetime import datetime,timedelta
random.seed(8); Base.metadata.drop_all(engine); Base.metadata.create_all(engine); db=SessionLocal()
owner=Role(name='OWNER'); manager=Role(name='MANAGER'); db.add_all([owner,manager]); db.flush(); db.add_all([User(name='Warehouse Owner',email='owner@smartwarehouse.com',password_hash=hash_password('Owner@123'),role_id=owner.id),User(name='Operations Manager',email='manager@smartwarehouse.com',password_hash=hash_password('Manager@123'),role_id=manager.id)])
ws=[Warehouse(name=f'Warehouse {x}',location=l,capacity=10000) for x,l in zip('ABCD',['Chennai North','Chennai South','Sriperumbudur','Oragadam'])]; db.add_all(ws); db.flush()
zones=[]
for w in ws:
 for x in 'ABC': zones.append(Zone(name=f'Zone {x}',warehouse_id=w.id,capacity=2500))
db.add_all(zones); db.flush(); db.add_all([Rack(code=f'{z.name.replace("Zone ","")}{n}',zone_id=z.id) for z in zones for n in range(1,4)])
sups=[Supplier(name=n,contact='procurement@example.com') for n in ['Alpha Industrial','Metro Components','Prime Safety','South Logistics','Titan Materials']]; db.add_all(sups); db.flush()
for i in range(1,121):
 stock=random.randint(0,280); minv=random.choice([15,20,30,50]);
 if i%19==0: stock=random.randint(0,8)
 p=Product(product_id=f'PRD-{i:04}',name=('Industrial Fasteners' if i==1 else f'{random.choice(["Hydraulic","Safety","Packaging","Electrical","Steel"])} {random.choice(["Kit","Component","Material","Assembly"])} {i}'),sku=f'SKU-{1000+i}',category=random.choice(['Hardware','Safety','Electrical','Packaging','Raw Material']),supplier_id=random.choice(sups).id,warehouse_id=random.choice(ws).id,zone=random.choice(['Zone A','Zone B','Zone C']),aisle='0'+str(random.randint(1,9)),rack='A'+str(random.randint(1,3)),shelf='S'+str(random.randint(1,4)),bin='B'+str(random.randint(1,8)),current_stock=stock,minimum_stock=minv,maximum_capacity=300,reorder_level=minv*1.5,unit='units',unit_price=random.randint(50,1200)); db.add(p); db.flush(); db.add(Inventory(product_id=p.id,quantity=stock)); db.add(InventoryTransaction(product_id=p.id,transaction_type='RECEIVING',quantity=stock,reference='OPENING',note='Opening balance'))
workers=[]
for i in range(1,45): workers.append(Worker(worker_id=f'WRK-{i:03}',name=f'Worker {i}',department=random.choice(['Receiving','Dispatch','Operations','Safety']),warehouse_id=random.choice(ws).id,shift='Day'))
db.add_all(workers); db.flush(); db.add_all([Attendance(worker_id=w.id,entry_time=datetime.now()-timedelta(hours=random.randint(1,8)),status=('PRESENT' if w.id%6 else 'ABSENT'),activity=random.choice(['Active','Loading','Inspection','Not working']),ppe_compliance='COMPLIANT') for w in workers])
cams=[Camera(camera_id=f'CAM-{i:02}',warehouse_id=random.choice(ws).id,zone=random.choice(['Zone A','Zone B','Receiving'])) for i in range(1,7)]; db.add_all(cams); db.flush()
for i in range(12):
 bad=i%4==0; db.add(SafetyEvent(worker_id=random.choice(workers).id,camera_id=random.choice(cams).id,warehouse_id=random.choice(ws).id,zone='Zone A',helmet=not bad,gloves=True,ppe_status='VIOLATION' if bad else 'COMPLIANT',violation_type='Helmet missing' if bad else None,confidence=.91,event_status='OPEN' if bad else 'CLOSED'))
for i in range(1,10):
 score=25 if i==1 else random.randint(58,98); db.add(Vehicle(vehicle_id=f'VEH-{i:02}',location=random.choice(['Dock 1','Zone A','Dispatch Bay','Charging']),zone='Zone A',speed=random.randint(0,24),battery=random.randint(15,96),temperature=random.randint(25,93),engine_status='RUNNING',health_score=score,maintenance_status='CRITICAL' if score<40 else 'NORMAL',operating_hours=random.randint(100,1000)))
for i in range(15): db.add(MaintenanceTask(title=f'{random.choice(["Vehicle","Rack","Forklift"])} inspection {i+1}',asset_type='Vehicle',asset_id=f'VEH-{i%9+1:02}',due_date=str((datetime.now()+timedelta(days=i-5)).date()),status='OVERDUE' if i<3 else 'SCHEDULED',priority='HIGH' if i<3 else 'NORMAL'))
for d in range(30):
 for w in ws: db.add(EnergyReading(warehouse_id=w.id,zone=random.choice(['Zone A','Zone B','Cold Storage']),power_kw=random.uniform(200,400),consumed_kwh=random.uniform(900,1900),reading_date=str((datetime.now()-timedelta(days=d)).date())))
db.add(EnergyCost(tariff=8.5,monthly_cost=364000)); db.add_all([AIInsight(severity='URGENT',title='Critical vehicle health',description='VEH-01 health score is below safe operating threshold.',module='vehicles',location='Zone A',action_url='/vehicles'),AIInsight(severity='ATTENTION',title='PPE violation detected',description='Helmet missing in Zone A.',module='cctv',location='Zone A',action_url='/cctv')]); db.add(Notification(title='Critical vehicle health',message='VEH-01 requires maintenance',severity='URGENT'))
db.commit(); print('Seeded',db.query(Product).count(),'products')
