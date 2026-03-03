from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security for admin
security = HTTPBasic()

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'nouakchottnight2024')


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Models
class Reservation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    date: str
    time: str
    guests: int
    message: Optional[str] = None
    status: str = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReservationCreate(BaseModel):
    name: str
    phone: str
    date: str
    time: str
    guests: int
    message: Optional[str] = None


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    price: int
    category: str
    image: Optional[str] = None
    is_available: bool = True


class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author: str
    rating: int
    comment: str
    date: str


class ContactInfo(BaseModel):
    phone: str = "+222 42 42 84 42"
    whatsapp: str = "+22242428442"
    address: str = "Cheikh Zayed, Nouakchott, Mauritanie"
    latitude: float = 18.0735
    longitude: float = -15.9582
    instagram: str = ""
    facebook: str = ""
    tiktok: str = ""


class Hours(BaseModel):
    day: str
    open_time: str
    close_time: str


# Routes

@api_router.get("/")
async def root():
    return {"message": "Nouakchott Night API"}


# Reservations
@api_router.post("/reservations", response_model=Reservation)
async def create_reservation(input: ReservationCreate):
    reservation = Reservation(**input.model_dump())
    doc = reservation.model_dump()
    await db.reservations.insert_one(doc)
    return reservation


@api_router.get("/reservations", response_model=List[Reservation])
async def get_reservations(admin: str = Depends(verify_admin)):
    reservations = await db.reservations.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return reservations


@api_router.patch("/reservations/{reservation_id}")
async def update_reservation_status(reservation_id: str, status: str, admin: str = Depends(verify_admin)):
    result = await db.reservations.update_one(
        {"id": reservation_id},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"message": "Status updated"}


@api_router.delete("/reservations/{reservation_id}")
async def delete_reservation(reservation_id: str, admin: str = Depends(verify_admin)):
    result = await db.reservations.delete_one({"id": reservation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return {"message": "Reservation deleted"}


# Menu
@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    menu_items = await db.menu.find({}, {"_id": 0}).to_list(1000)
    if not menu_items:
        # Return default menu items if none in DB
        return get_default_menu()
    return menu_items


def get_default_menu():
    return [
        # Plats Chauds - Pâtes
        {"id": "1", "name": "Tagliatelle Carbonara", "name_ar": "تاكلياتل كاربونارا", "price": 350, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=400", "is_available": True},
        {"id": "2", "name": "Spaghetti Bolognaise", "name_ar": "اسباكتي بولونيز", "price": 320, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1622973536968-3ead9e780960?w=400", "is_available": True},
        {"id": "3", "name": "Tagliatelles aux Fruits de Mer", "name_ar": "تاكلياتل أو فريوي دي مير", "description": "Calamars, crevettes", "price": 500, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400", "is_available": True},
        {"id": "4", "name": "Tagliatelles Pesto aux Crevettes", "name_ar": "تاكلياتل بستو أو كريفت", "description": "Sauce pesto crevette", "price": 500, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=400", "is_available": True},
        {"id": "5", "name": "Beignet de Crevettes Sauce Aigre", "name_ar": "بينيت دي كريفت سوس أكر", "price": 400, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400", "is_available": True},
        {"id": "6", "name": "Lasagne", "name_ar": "لازان", "price": 380, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1574894709920-11b28e7367e3?w=400", "is_available": True},
        {"id": "7", "name": "Pané au Fruit de Mer", "name_ar": "باني أوفريوي دي مير", "price": 500, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400", "is_available": True},
        {"id": "8", "name": "Pané Poulet Sauce Champignon", "name_ar": "باني بولي سوس شامبينيوه", "price": 400, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400", "is_available": True},
        {"id": "9", "name": "Tagliatelles Poulet ou Viande", "name_ar": "تاكلياتل بولي أو فياند", "price": 350, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1556761223-4c4282c73f77?w=400", "is_available": True},
        {"id": "10", "name": "Spaghettis Poulet ou Viande à la Crème", "name_ar": "سباكتي بولي أو فياند كريم", "price": 350, "category": "Pâtes", "image": "https://images.unsplash.com/photo-1608897013039-887f21d8c804?w=400", "is_available": True},
        
        # Milkshakes
        {"id": "11", "name": "Milkshake Chocolat", "name_ar": "ميلشيك شوكولا", "price": 150, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400", "is_available": True},
        {"id": "12", "name": "Milkshake Fraise", "name_ar": "ميلشيك فريز", "price": 150, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=400", "is_available": True},
        {"id": "13", "name": "Milkshake Vanille", "name_ar": "ميلشيك فريز", "price": 150, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1568901839119-631418a3910d?w=400", "is_available": True},
        {"id": "14", "name": "Milkshake Avocat", "name_ar": "ميلشيك آفوكا", "price": 150, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1638176066666-ffb2f013c7dd?w=400", "is_available": True},
        {"id": "15", "name": "Milkshake Lotus", "name_ar": "ميلشيك لوتيس", "price": 180, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=400", "is_available": True},
        {"id": "16", "name": "Milkshake Oréo", "name_ar": "ميلشيك أوريو", "price": 180, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400", "is_available": True},
        {"id": "17", "name": "Zrig Nouakchott Night", "name_ar": "ازريك نواكشوط نايت", "price": 160, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1541658016709-82535e94bc69?w=400", "is_available": True},
        {"id": "18", "name": "Milkshake Cerelac", "name_ar": "ميلشيك سيريلاك", "price": 180, "category": "Milkshakes", "image": "https://images.unsplash.com/photo-1577805947697-89e18249d767?w=400", "is_available": True},
        
        # Salades de Fruits
        {"id": "19", "name": "Salade de Fruits Classic", "name_ar": "سلات دي فريوي كلاسيك", "price": 150, "category": "Fruits", "image": "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?w=400", "is_available": True},
        {"id": "20", "name": "Salade de Fruits Nouakchott Night", "name_ar": "سلات دي فريوي نواكشوط نايت", "price": 200, "category": "Fruits", "image": "https://images.unsplash.com/photo-1564093497595-593b96d80180?w=400", "is_available": True},
        {"id": "21", "name": "Assiette de Fruits", "name_ar": "آسيت دي فريوي", "price": 300, "category": "Fruits", "image": "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=400", "is_available": True},
        
        # Desserts
        {"id": "22", "name": "Gaufre Sucrée", "name_ar": "كوفر سيكري", "price": 120, "category": "Desserts", "image": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=400", "is_available": True},
        {"id": "23", "name": "Gaufre Nutella", "name_ar": "كوفر نيتلا", "price": 150, "category": "Desserts", "image": "https://images.unsplash.com/photo-1598121444850-a3f89e60a1ee?w=400", "is_available": True},
        {"id": "24", "name": "Gaufre Nutella Banane", "name_ar": "كوفر نيتلا بانان", "price": 170, "category": "Desserts", "image": "https://images.unsplash.com/photo-1568051243851-f9b136146e97?w=400", "is_available": True},
        {"id": "25", "name": "Crêpe Sucrée", "name_ar": "كريب سيكري", "price": 120, "category": "Desserts", "image": "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=400", "is_available": True},
        {"id": "26", "name": "Crêpe Nutella", "name_ar": "كريب نيتلا", "price": 150, "category": "Desserts", "image": "https://images.unsplash.com/photo-1584365685547-9a5fb6f3a70c?w=400", "is_available": True},
        {"id": "27", "name": "Crêpe Nutella Banane", "name_ar": "كريب نيتلا بانان", "price": 170, "category": "Desserts", "image": "https://images.unsplash.com/photo-1587314168485-3236d6710814?w=400", "is_available": True},
        {"id": "28", "name": "1 Boule Glace", "name_ar": "1 بول اكلاس", "price": 50, "category": "Glaces", "image": "https://images.unsplash.com/photo-1567206563064-6f60f40a2b57?w=400", "is_available": True},
        {"id": "29", "name": "2 Boules Glace", "name_ar": "2 بول اكلاس", "price": 100, "category": "Glaces", "image": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=400", "is_available": True},
        {"id": "30", "name": "3 Boules Glace", "name_ar": "3 بول اكلاس", "price": 150, "category": "Glaces", "image": "https://images.unsplash.com/photo-1557142046-c704a3adf364?w=400", "is_available": True},
        {"id": "31", "name": "Banana Split", "name_ar": "بانانا سبليت", "price": 200, "category": "Glaces", "image": "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400", "is_available": True},
        {"id": "32", "name": "Pop-corn PM", "name_ar": "بوب كورن ب.م", "price": 60, "category": "Snacks", "image": "https://images.unsplash.com/photo-1585647347483-22b66260dfff?w=400", "is_available": True},
        {"id": "33", "name": "Pop-corn GM", "name_ar": "بوب كورن ج.م", "price": 90, "category": "Snacks", "image": "https://images.unsplash.com/photo-1578849278619-e73505e9610f?w=400", "is_available": True},
        {"id": "34", "name": "Fondant au Chocolat", "name_ar": "فوندان أو شوكولا", "price": 200, "category": "Desserts", "image": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=400", "is_available": True},
        {"id": "35", "name": "Crêpes Complet", "name_ar": "كريب كومبلي", "price": 200, "category": "Desserts", "image": "https://images.unsplash.com/photo-1565299543923-37dd37887442?w=400", "is_available": True},
        {"id": "36", "name": "Dessert Nouakchott Night", "name_ar": "ديسير نواكشوط نايت", "price": 300, "category": "Desserts", "image": "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=400", "is_available": True},
        {"id": "37", "name": "Pancakes", "name_ar": "بانكيك", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400", "is_available": True},
        {"id": "38", "name": "Crème Brûlée", "name_ar": "كريم بريلي", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?w=400", "is_available": True},
        {"id": "39", "name": "Cookies", "name_ar": "كوكيس", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400", "is_available": True},
        {"id": "40", "name": "Brownies", "name_ar": "براونيز", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400", "is_available": True},
        {"id": "41", "name": "Churros au Chocolat", "name_ar": "شوروس أو شوكلا", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1624371414361-e670edf4e53f?w=400", "is_available": True},
        {"id": "42", "name": "Cheesecake Lotus", "name_ar": "تشيز كايك لوتيس", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=400", "is_available": True},
        {"id": "43", "name": "Cheesecake Oreo", "name_ar": "تشيز كايك أوريو", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1578775887804-699de7086ff9?w=400", "is_available": True},
        {"id": "44", "name": "Cheesecake Fruit Rouge", "name_ar": "تشيز كايك فريوي روج", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1508737027454-e6454ef45afd?w=400", "is_available": True},
        {"id": "45", "name": "Tiramisu", "name_ar": "تيراميسو", "price": 180, "category": "Desserts", "image": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400", "is_available": True},
        {"id": "46", "name": "French Toast", "name_ar": "فرينش تواست", "price": 200, "category": "Desserts", "image": "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=400", "is_available": True},
        {"id": "47", "name": "Crêpes Rolls Oreo", "name_ar": "كريب رولس أوريو", "price": 200, "category": "Desserts", "image": "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=400", "is_available": True},
    ]


# Reviews
@api_router.get("/reviews", response_model=List[Review])
async def get_reviews():
    reviews = await db.reviews.find({}, {"_id": 0}).to_list(100)
    if not reviews:
        return get_default_reviews()
    return reviews


def get_default_reviews():
    return [
        {"id": "1", "author": "Mohamed A.", "rating": 5, "comment": "Ambiance incroyable ! Le meilleur endroit de Nouakchott pour passer une soirée entre amis. Service impeccable.", "date": "2024-01-15"},
        {"id": "2", "author": "Fatima B.", "rating": 4, "comment": "Les pâtes aux fruits de mer sont excellentes. J'adore la piscine et les lumières. À refaire !", "date": "2024-01-10"},
        {"id": "3", "author": "Ahmed K.", "rating": 5, "comment": "Happy hour génial ! Les milkshakes sont délicieux. L'endroit parfait pour se détendre.", "date": "2024-01-05"},
        {"id": "4", "author": "Mariam S.", "rating": 4, "comment": "Cadre magnifique, surtout la nuit avec toutes les lumières. Un peu d'attente mais ça vaut le coup.", "date": "2023-12-28"},
    ]


# Contact Info
@api_router.get("/contact")
async def get_contact():
    return ContactInfo()


# Hours
@api_router.get("/hours")
async def get_hours():
    return [
        {"day": "Dimanche", "open_time": "17h00", "close_time": "2h00"},
        {"day": "Lundi", "open_time": "17h00", "close_time": "2h00"},
        {"day": "Mardi", "open_time": "17h00", "close_time": "2h00"},
        {"day": "Mercredi", "open_time": "17h00", "close_time": "2h00"},
        {"day": "Jeudi", "open_time": "17h00", "close_time": "3h00"},
        {"day": "Vendredi", "open_time": "17h00", "close_time": "2h00"},
        {"day": "Samedi", "open_time": "17h00", "close_time": "2h00"},
    ]


# Stats for admin
@api_router.get("/stats")
async def get_stats(admin: str = Depends(verify_admin)):
    total_reservations = await db.reservations.count_documents({})
    pending = await db.reservations.count_documents({"status": "pending"})
    confirmed = await db.reservations.count_documents({"status": "confirmed"})
    cancelled = await db.reservations.count_documents({"status": "cancelled"})
    
    return {
        "total": total_reservations,
        "pending": pending,
        "confirmed": confirmed,
        "cancelled": cancelled
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
