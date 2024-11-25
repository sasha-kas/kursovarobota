import mysql.connector
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/img", StaticFiles(directory="img"), name="img")
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sashamysql2",
    "database": "kursach"
}

# Моделі для запису на прийом
class Appointment(BaseModel):
    doctorId: int
    appointmentDate: datetime
    description: str
    serviceIds: list[int]

class Owner(BaseModel):
    firstName: str
    lastName: str
    phone: str
    address: str

class Patient(BaseModel):
    name: str
    species: str
    breed: str
    birthDate: str

class VisitRequest(BaseModel):
    owner: Owner
    patient: Patient
    appointment: Appointment

# Підключення до бази даних
def get_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Отримати список лікарів
@app.get("/doctors", response_model=list[dict])
async def get_doctors():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT DoctorID, FirstName, LastName, Specialization FROM Doctors")
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Отримати список послуг
@app.get("/services", response_model=list[dict])
async def get_services():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT ServiceID, ServiceName, Price FROM Services")
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Допоміжні функції
def get_owner_id_by_phone(cursor, phone):
    # Уникаємо пробілів і приводимо до єдиного формату перед перевіркою
    normalized_phone = ''.join(filter(str.isdigit, phone))  # Залишаємо лише цифри
    query = "SELECT OwnerID FROM Owners WHERE REPLACE(Phone, ' ', '') = %s"
    cursor.execute(query, (normalized_phone,))
    return cursor.fetchone()


def add_new_owner(cursor, first_name, last_name, phone, address):
    query = """
    INSERT INTO Owners (FirstName, LastName, Phone, Address)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (first_name, last_name, phone, address))
    return cursor.lastrowid

def add_patient(cursor, name, species, breed, birth_date, owner_id):
    query = """
    INSERT INTO Patients (Name, Species, Breed, BirthDate, OwnerID)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, species, breed, birth_date, owner_id))
    return cursor.lastrowid

def add_appointment(cursor, patient_id, doctor_id, visit_date, notes):
    query = """
    INSERT INTO Visits (PatientID, DoctorID, VisitDate, Notes)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (patient_id, doctor_id, visit_date, notes))
    return cursor.lastrowid

def add_visit_services(cursor, visit_id, service_ids):
    query = """
    INSERT INTO VisitServices (VisitID, ServiceID)
    VALUES (%s, %s)
    """
    for service_id in service_ids:
        cursor.execute(query, (visit_id, service_id))

# Маршрут для створення запису на прийом
@app.post("/visit")
def create_visit(visit: VisitRequest):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Отримуємо або створюємо власника
        owner = get_owner_id_by_phone(cursor, visit.owner.phone)
        if owner:
            owner_id = owner['OwnerID']
        else:
            owner_id = add_new_owner(
                cursor,
                visit.owner.firstName,
                visit.owner.lastName,
                visit.owner.phone,
                visit.owner.address,
            )
            conn.commit()

        # Додаємо пацієнта
        patient_id = add_patient(
            cursor,
            visit.patient.name,
            visit.patient.species,
            visit.patient.breed,
            datetime.strptime(visit.patient.birthDate, "%Y-%m-%d").date(),
            owner_id,
        )
        conn.commit()

        # Додаємо запис на прийом
        visit_id = add_appointment(
            cursor,
            patient_id,
            visit.appointment.doctorId,
            visit.appointment.appointmentDate,
            visit.appointment.description,
        )
        conn.commit()

        # Додаємо послуги для запису
        add_visit_services(cursor, visit_id, visit.appointment.serviceIds)
        conn.commit()

        return {"message": "Запис на прийом успішно створено"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# Головна сторінка
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
