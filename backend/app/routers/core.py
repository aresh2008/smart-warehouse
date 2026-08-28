from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import get_db
from ..models import *
from ..schemas import *
from ..auth import current,roles,verify,token
r=APIRouter(prefix='/api')
def product_out(p):
 return {'id':p.id,'product_id':p.product_id,'name':p.name,'sku':p.sku,'category':p.category,'supplier_id':p.supplier_id,'supplier':p.supplier.name if p.supplier else '', 'warehouse_id':p.warehouse_id,'warehouse':p.warehouse.name if p.warehouse else '', 'zone':p.zone,'aisle':p.aisle,'rack':p.rack,'shelf':p.shelf,'bin':p.bin,'current_stock':p.current_stock,'minimum_stock':p.minimum_stock,'maximum_capacity':p.maximum_capacity,'reorder_level':p.reorder_level,'unit':p.unit,'unit_price':p.unit_price,'expiry_date':p.expiry_date,'stock_status':'OUT OF STOCK' if p.current_stock<=0 else 'CRITICAL' if p.current_stock<=p.minimum_stock else 'LOW STOCK' if p.current_stock<=p.reorder_level else 'HEALTHY'}
@r.post('/auth/login')
def login(x:Login,db:Session=Depends(get_db)):
 u=db.query(User).filter(User.email==x.email).first()
 if not u or not verify(x.password,u.password_hash): raise HTTPException(401,'Invalid email or password')
 return {'access_token':token(u),'user':{'name':u.name,'email':u.email,'role':u.role.name}}
@r.get('/dashboard')
def dashboard(db:Session=Depends(get_db),u=Depends(current)):
 ps=db.query(Product).all(); low=[p for p in ps if p.current_stock<=p.reorder_level]; priorities=[]
 for p in [p for p in ps if p.current_stock<=p.minimum_stock][:6]: priorities.append({'severity':'URGENT' if p.current_stock<=0 else 'HIGH PRIORITY','title':f'{p.name} stock risk','description':f'{p.current_stock:g} {p.unit} available; reorder level is {p.reorder_level:g}.','timestamp':str(p.updated_at),'module':'Inventory','location':p.warehouse.name,'action_url':f'/inventory/{p.id}'})
 priorities += [{'severity':x.severity,'title':x.title,'description':x.description,'timestamp':str(x.created_at),'module':x.module,'location':x.location,'action_url':x.action_url} for x in db.query(AIInsight).filter(AIInsight.status=='OPEN').all()]
 return {'metrics':{'products':len(ps),'low_stock':len(low),'workers_present':db.query(Attendance).filter(Attendance.status=='PRESENT').count(),'critical_vehicles':db.query(Vehicle).filter(Vehicle.health_score<40).count(),'open_safety_events':db.query(SafetyEvent).filter(SafetyEvent.ppe_status=='VIOLATION',SafetyEvent.event_status=='OPEN').count()},'priorities':priorities[:10]}
@r.get('/inventory')
def inventory(search:str='',category:str='',warehouse_id:int=0,status:str='',db:Session=Depends(get_db),u=Depends(current)):
 q=db.query(Product)
 if search:q=q.filter((Product.name.ilike(f'%{search}%'))|(Product.sku.ilike(f'%{search}%')))
 if category:q=q.filter(Product.category==category)
 if warehouse_id:q=q.filter(Product.warehouse_id==warehouse_id)
 data=[product_out(p) for p in q.all()]
 return [p for p in data if not status or p['stock_status']==status]
@r.post('/inventory')
def create_product(x:ProductIn,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 p=Product(**x.model_dump());db.add(p);db.flush();db.add(Inventory(product_id=p.id,quantity=p.current_stock));db.commit();return product_out(p)
@r.get('/inventory/transactions')
def transactions(product_id:int=0,db:Session=Depends(get_db),u=Depends(current)):
 q=db.query(InventoryTransaction)
 if product_id:q=q.filter_by(product_id=product_id)
 return [{'id':x.id,'product':x.product.name,'type':x.transaction_type,'quantity':x.quantity,'reference':x.reference,'note':x.note,'created_at':x.created_at} for x in q.order_by(InventoryTransaction.id.desc()).limit(100)]
@r.get('/inventory/{id}')
def one_product(id:int,db:Session=Depends(get_db),u=Depends(current)):
 p=db.get(Product,id)
 if not p:raise HTTPException(404,'Product not found')
 o=product_out(p); tx=db.query(InventoryTransaction).filter_by(product_id=id).order_by(InventoryTransaction.id.desc()).limit(30).all(); o['history']=[{'type':x.transaction_type,'quantity':x.quantity,'reference':x.reference,'date':x.created_at} for x in tx];o['daily_usage']=max(1,round(sum(-x.quantity for x in tx if x.quantity<0)/max(1,len(tx)),1));o['days_remaining']=round(p.current_stock/o['daily_usage'],1);o['recommendation']='REORDER NOW' if p.current_stock<=p.reorder_level else 'Stock level healthy';return o
@r.put('/inventory/{id}')
def update_product(id:int,x:ProductIn,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 p=db.get(Product,id)
 if not p:raise HTTPException(404,'Product not found')
 for k,v in x.model_dump().items():setattr(p,k,v)
 db.commit();return product_out(p)
@r.delete('/inventory/{id}')
def delete_product(id:int,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 p=db.get(Product,id)
 if not p:raise HTTPException(404,'Product not found')
 db.delete(p);db.commit();return {'ok':True}
@r.post('/inventory/{id}/adjust')
def adjust(id:int,x:StockAdjust,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 p=db.get(Product,id)
 if not p:raise HTTPException(404,'Product not found')
 if p.current_stock+x.quantity<0:raise HTTPException(400,'Stock cannot be negative')
 p.current_stock+=x.quantity;db.add(InventoryTransaction(product_id=id,transaction_type='ADJUSTMENT',quantity=x.quantity,reference='MANUAL',note=x.note));db.commit();return product_out(p)
@r.get('/receiving')
def receiving(db:Session=Depends(get_db),u=Depends(current)):return [{'id':x.id,'invoice_number':x.invoice_number,'vehicle':x.vehicle,'warehouse':x.warehouse.name,'status':x.status,'tolerance':x.tolerance,'created_at':x.created_at,'items':[{'id':i.id,'product':i.product.name,'product_id':i.product_id,'expected_qty':i.expected_qty,'detected_qty':i.detected_qty,'confidence':i.confidence,'expected_weight':i.expected_weight,'actual_weight':i.actual_weight} for i in x.items]} for x in db.query(Receiving).order_by(Receiving.id.desc()).all()]
@r.post('/receiving')
def receiving_create(x:ReceivingIn,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 a=Receiving(invoice_number=x.invoice_number,vehicle=x.vehicle,warehouse_id=x.warehouse_id,tolerance=x.tolerance);db.add(a);db.flush()
 for i in x.items:db.add(ReceivingItem(receiving_id=a.id,product_id=i['product_id'],expected_qty=i['expected_qty'],expected_weight=i.get('expected_weight',i['expected_qty'])))
 db.commit();return {'id':a.id,'status':a.status}
@r.post('/receiving/{id}/verify')
def receiving_verify(id:int,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 a=db.get(Receiving,id)
 if not a:raise HTTPException(404,'Receiving not found')
 mismatch=False
 for i in a.items:
  i.detected_qty=round(i.expected_qty*(.85 if i.id%5==0 else 1),2);i.confidence=.94;i.actual_weight=i.detected_qty
  if abs(i.detected_qty-i.expected_qty)/i.expected_qty*100>a.tolerance:mismatch=True
 a.status='MISMATCH' if mismatch else 'MATCHED';a.verified_at=datetime.now()
 if mismatch:db.add(Notification(title='Receiving mismatch',message=f'Invoice {a.invoice_number} requires review',severity='URGENT'))
 db.commit();return {'id':id,'status':a.status}
@r.post('/receiving/{id}/approve')
def receiving_approve(id:int,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 a=db.get(Receiving,id)
 if not a or a.status not in ['MATCHED','MISMATCH']:raise HTTPException(400,'Verify receiving first')
 for i in a.items:
  qty=i.detected_qty if i.detected_qty is not None else i.expected_qty;i.product.current_stock+=qty;db.add(InventoryTransaction(product_id=i.product_id,transaction_type='RECEIVING',quantity=qty,reference=a.invoice_number,note='Approved receiving'))
 a.status='APPROVED';db.commit();return {'status':'APPROVED'}
@r.post('/receiving/{id}/reject')
def receiving_reject(id:int,db:Session=Depends( get_db),u=Depends(roles('OWNER','MANAGER'))):
 a=db.get(Receiving,id);a.status='REJECTED';db.commit();return {'status':'REJECTED'}
@r.post('/dispatch')
def dispatch(x:DispatchIn,db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 p=db.get(Product,x.product_id)
 if not p or p.current_stock<x.quantity:raise HTTPException(400,'Insufficient stock')
 p.current_stock-=x.quantity;d=StockDispatch(**x.model_dump());db.add(d);db.add(InventoryTransaction(product_id=p.id,transaction_type='DISPATCH',quantity=-x.quantity,reference=x.customer_order,note=f'Dispatch to {x.destination}'));db.commit();return {'id':d.id,'remaining_stock':p.current_stock,'recommendation':'REORDER' if p.current_stock<=p.reorder_level else 'HEALTHY'}
@r.get('/dispatch')
def dispatches(db:Session=Depends(get_db),u=Depends(current)):return [{'id':x.id,'product':x.product.name,'quantity':x.quantity,'destination':x.destination,'vehicle':x.vehicle,'status':x.status,'created_at':x.created_at} for x in db.query(StockDispatch).order_by(StockDispatch.id.desc()).all()]

@r.get('/cctv/feeds')
def feeds(db:Session=Depends(get_db),u=Depends(current)):return [{'camera_id':c.camera_id,'zone':c.zone,'warehouse_id':c.warehouse_id,'status':c.status,'mode':'DEMO / SYNTHETIC OPENCV'} for c in db.query(Camera).all()]
@r.get('/cctv/events')
def events(db:Session=Depends(get_db),u=Depends(current)):return [{'id':e.id,'worker':e.worker.name,'camera':e.camera.camera_id,'zone':e.zone,'helmet':e.helmet,'gloves':e.gloves,'ppe_status':e.ppe_status,'violation_type':e.violation_type,'confidence':e.confidence,'status':e.event_status,'created_at':e.created_at} for e in db.query(SafetyEvent).order_by(SafetyEvent.id.desc()).all()]
@r.post('/cctv/simulate-event')
def simulate_cctv(db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 import random
 w=random.choice(db.query(Worker).all());c=random.choice(db.query(Camera).all());bad=random.choice([True,False,False]);e=SafetyEvent(worker_id=w.id,camera_id=c.id,warehouse_id=w.warehouse_id,zone=c.zone,helmet=not bad,gloves=True,ppe_status='VIOLATION' if bad else 'COMPLIANT',violation_type='Helmet missing' if bad else None,confidence=.93,event_status='OPEN' if bad else 'CLOSED');db.add(e)
 a=db.query(Attendance).filter_by(worker_id=w.id).first();a.status='PRESENT';a.activity='Active';a.ppe_compliance=e.ppe_status
 if bad:db.add(Notification(title='PPE violation',message=f'{w.name}: Helmet missing',severity='URGENT'))
 db.commit();return {'status':e.ppe_status,'worker':w.name}
@r.get('/workers')
def workers(db:Session=Depends(get_db),u=Depends(current)):return [{'id':w.id,'worker_id':w.worker_id,'name':w.name,'department':w.department,'warehouse':w.warehouse.name,'shift':w.shift} for w in db.query(Worker).all()]
@r.get('/attendance')
def attendance(db:Session=Depends(get_db),u=Depends(current)):
 a=db.query(Attendance).all();return {'summary':{'total':len(a),'present':sum(x.status=='PRESENT' for x in a),'absent':sum(x.status=='ABSENT' for x in a),'active':sum(x.activity=='Active' for x in a),'not_working':sum(x.activity=='Not working' for x in a),'violations':db.query(SafetyEvent).filter(SafetyEvent.ppe_status=='VIOLATION',SafetyEvent.event_status=='OPEN').count()},'records':[{'id':x.id,'worker':x.worker.name,'department':x.worker.department,'status':x.status,'activity':x.activity,'ppe':x.ppe_compliance,'entry_time':x.entry_time} for x in a]}
@r.get('/vehicles')
def vehicles(db:Session=Depends(get_db),u=Depends(current)):return [{'id':v.id,'vehicle_id':v.vehicle_id,'location':v.location,'zone':v.zone,'speed':v.speed,'battery':v.battery,'temperature':v.temperature,'engine_status':v.engine_status,'health_score':v.health_score,'maintenance_status':v.maintenance_status,'last_update':v.updated_at} for v in db.query(Vehicle).all()]
@r.get('/vehicles/{id}')
def vehicle(id:int,db:Session=Depends(get_db),u=Depends(current)):
 v=db.get(Vehicle,id)
 if not v:raise HTTPException(404,'Vehicle not found')
 return {'id':v.id,'vehicle_id':v.vehicle_id,'location':v.location,'zone':v.zone,'speed':v.speed,'battery':v.battery,'temperature':v.temperature,'health_score':v.health_score,'maintenance_status':v.maintenance_status,'operating_hours':v.operating_hours}
@r.get('/vehicles/{id}/health')
def vehicle_health(id:int,db:Session=Depends(get_db),u=Depends(current)):
 v=db.get(Vehicle,id);return {'vehicle_id':v.vehicle_id,'health_score':v.health_score,'status':'CRITICAL' if v.health_score<40 else 'WARNING' if v.health_score<70 else 'NORMAL','recommendation':'Stop and schedule maintenance' if v.health_score<40 else 'Continue monitoring'}
@r.post('/vehicles/simulate')
def vehicle_simulate(db:Session=Depends(get_db),u=Depends(roles('OWNER','MANAGER'))):
 import random
 changed=[]
 for v in db.query(Vehicle).all():
  v.speed=max(0,min(35,v.speed+random.randint(-5,5)));v.battery=max(5,min(100,v.battery+random.randint(-6,2)));v.temperature=max(20,min(105,v.temperature+random.randint(-4,5)));v.operating_hours+=.1;v.health_score=round(max(5,min(100,100-(100-v.battery)*.35-max(0,v.temperature-75)*.8)),1);v.maintenance_status='CRITICAL' if v.health_score<40 else 'WARNING' if v.health_score<70 else 'NORMAL';db.add(VehicleSensor(vehicle_id=v.id,speed=v.speed,temperature=v.temperature,battery=v.battery,vibration=random.random()*5,operating_hours=v.operating_hours));changed.append(v.vehicle_id)
 db.commit();return {'updated':changed}
@r.get('/warehouse/map')
def warehouse_map(db:Session=Depends(get_db),u=Depends(current)):return {'warehouses':[{'id':w.id,'name':w.name,'location':w.location,'capacity':w.capacity,'zones':[{'id':z.id,'name':z.name,'capacity':z.capacity,'racks':[x.code for x in db.query(Rack).filter_by(zone_id=z.id)]} for z in db.query(Zone).filter_by(warehouse_id=w.id)]} for w in db.query(Warehouse).all()],'vehicles':[{'id':v.id,'label':v.vehicle_id,'location':v.location,'health':v.health_score} for v in db.query(Vehicle).all()],'cameras':[{'id':c.id,'label':c.camera_id,'zone':c.zone} for c in db.query(Camera).all()]}
@r.get('/energy')
def energy(db:Session=Depends(get_db),u=Depends(roles('OWNER'))):return [{'date':x.reading_date,'zone':x.zone,'power_kw':x.power_kw,'consumed_kwh':x.consumed_kwh} for x in db.query(EnergyReading).order_by(EnergyReading.id.desc()).limit(120)]
@r.get('/energy/summary')
def energy_summary(db:Session=Depends(get_db),u=Depends(roles('OWNER'))):
 rs=db.query(EnergyReading).all();tariff=db.query(EnergyCost).first().tariff;today=str(datetime.now().date());today_kwh=sum(x.consumed_kwh for x in rs if x.reading_date==today);month_kwh=sum(x.consumed_kwh for x in rs);return {'current_power':round(sum(x.power_kw for x in rs[-4:]),1),'today_consumption':round(today_kwh,1),'monthly_consumption':round(month_kwh/1000,1),'tariff':tariff,'estimated_monthly_cost':round(month_kwh*tariff,2),'zone_consumption':[{'zone':z,'kwh':round(sum(x.consumed_kwh for x in rs if x.zone==z),1)} for z in set(x.zone for x in rs)]}
@r.post('/chat')
def chat(x:ChatIn,db:Session=Depends(get_db),u=Depends(current)):
 q=x.question.lower();answer="I don't have enough data to answer that."
 ps=db.query(Product).all()
 if 'low' in q and 'stock' in q:answer=f'{sum(p.current_stock<=p.reorder_level for p in ps)} products are at or below their reorder level.'
 elif 'run out' in q:answer='Products likely to run out soon: '+', '.join(p.name for p in ps if p.current_stock<=p.reorder_level)[:8]
 elif 'current stock of' in q:
  name=q.split('current stock of',1)[1].strip();p=next((p for p in ps if name in p.name.lower()),None);answer=f'{p.name} has {p.current_stock:g} {p.unit} in stock.' if p else "I don't have enough data to answer that."
 elif 'highest inventory' in q:
  w=max(db.query(Warehouse).all(),key=lambda w:sum(p.current_stock for p in ps if p.warehouse_id==w.id));answer=f'{w.name} has the highest inventory, with {sum(p.current_stock for p in ps if p.warehouse_id==w.id):g} units.'
 elif 'vehicle' in q and 'critical' in q:
  vs=[v.vehicle_id for v in db.query(Vehicle).filter(Vehicle.health_score<40)];answer='Critical vehicles: '+(', '.join(vs) if vs else 'none')
 elif 'workers' in q and 'present' in q:answer=f'{db.query(Attendance).filter(Attendance.status=="PRESENT").count()} workers are present.'
 elif 'receiving' in q and 'mismatch' in q:answer=f'{db.query(Receiving).filter(Receiving.status=="MISMATCH").count()} receiving transactions have mismatches.'
 db.add(ChatHistory(user_id=u.id,question=x.question,answer=answer));db.commit();return {'answer':answer}
@r.get('/analytics')
def analytics(db:Session=Depends(get_db),u=Depends(current)):
 return {'stock_predictions':[{'product':p.name,'current_stock':p.current_stock,'daily_usage':max(1,round(p.reorder_level/7,1)),'days_remaining':round(p.current_stock/max(1,p.reorder_level/7),1),'recommendation':'REORDER' if p.current_stock<=p.reorder_level else 'MONITOR','confidence':.82} for p in db.query(Product).order_by(Product.current_stock).limit(12)],'capacity_risk':round(sum(p.current_stock for p in db.query(Product))/sum(p.maximum_capacity for p in db.query(Product))*100,1)}
@r.get('/maintenance')
def maintenance(db:Session=Depends(get_db),u=Depends(current)):return [{'id':x.id,'title':x.title,'asset_type':x.asset_type,'asset_id':x.asset_id,'due_date':x.due_date,'status':x.status,'priority':x.priority} for x in db.query(MaintenanceTask).all()]
@r.get('/notifications')
def notifications(db:Session=Depends(get_db),u=Depends(current)):return [{'id':x.id,'title':x.title,'message':x.message,'severity':x.severity,'read':x.read,'created_at':x.created_at} for x in db.query(Notification).order_by(Notification.id.desc()).all()]
@r.get('/reports')
def reports(kind:str='inventory',db:Session=Depends(get_db),u=Depends(current)):
 if kind=='financial' and u.role.name!='OWNER':raise HTTPException(403,'Owner permission required')
 data={'inventory':inventory(db=db,u=u),'receiving':receiving(db=db,u=u),'dispatch':dispatches(db=db,u=u),'attendance':attendance(db=db,u=u),'vehicle':vehicles(db=db,u=u),'maintenance':maintenance(db=db,u=u)}
 if kind=='financial':data={'monthly_expenses':425000,'energy_cost':energy_summary(db=db,u=u)['estimated_monthly_cost'],'vehicle_operating_cost':38000,'maintenance_cost':52000,'inventory_purchase_cost':190000,'operational_cost':145000}
 return {'type':kind,'data':data.get(kind,events(db=db,u=u))}
