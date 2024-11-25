

async function loadFormData() {
    try {

        const [doctorsResponse, servicesResponse] = await Promise.all([
            fetch('http://127.0.0.1:8000/doctors'),
            fetch('http://127.0.0.1:8000/services')
        ]);

        // Перевіряємо статус відповіді
        if (!doctorsResponse.ok || !servicesResponse.ok) {
            throw new Error('Помилка завантаження даних: ' +
                `Лікарі: ${doctorsResponse.status}, Послуги: ${servicesResponse.status}`);
        }

        const doctors = await doctorsResponse.json();
        const services = await servicesResponse.json();

        const doctorSelect = document.querySelector('select[name="doctorId"]');
        const serviceSelect = document.querySelector('select[name="serviceId"]');

        if (!doctorSelect || !serviceSelect) {
            console.error('Не вдалося знайти елементи select');
            return;
        }

        // Очищення списків перед додаванням
        doctorSelect.innerHTML = '<option value="">Оберіть лікаря</option>';
        serviceSelect.innerHTML = '<option value="">Оберіть послугу</option>';

        // Додаємо лікарів до списку
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.DoctorID;
            option.textContent = `${doctor.FirstName} ${doctor.LastName} (${doctor.Specialization})`;
            doctorSelect.appendChild(option);
        });

        // Додаємо послуги до списку
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.ServiceID;
            option.textContent = `${service.ServiceName} (${parseFloat(service.Price).toFixed(2)} грн)`;
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Помилка завантаження даних:', error);
    }
}

// Показати форму запису
function showAppointmentForm() {
    const appointmentForm = document.getElementById('appointment');
    if (appointmentForm) {
        appointmentForm.style.display = 'block';
        appointmentForm.scrollIntoView({ behavior: 'smooth' });
    }
}

// Відправка всіх даних форми
async function submitAppointment(event) {
    event.preventDefault();

    const form = event.target;
    try {
        // Формуємо payload з даними власника, пацієнта та прийому
        const formData = {
            owner: {
                firstName: form.ownerFName.value.trim(),
                lastName: form.ownerLName.value.trim(),
                phone: form.phone.value.trim(),
                address: form.address.value.trim()
            },
            patient: {
                name: form.patientName.value.trim(),
                species: form.species.value.trim(),
                breed: form.breed.value.trim(),
                birthDate: form.birthDate.value
            },
            appointment: {
                doctorId: parseInt(form.doctorId.value),
                appointmentDate: form.appointmentDateTime.value,
                description: form.description.value.trim(),
                serviceIds: [parseInt(form.serviceId.value)]
            }
        };

        // Перевірка обов'язкових полів
        if (!formData.owner.phone || !formData.patient.name || !formData.appointment.doctorId) {
            throw new Error('Будь ласка, заповніть усі обов\'язкові поля.');
        }

        const response = await fetch('http://127.0.0.1:8000/visit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Запис на прийом успішно створено!');
            form.reset();
            document.getElementById('appointment').style.display = 'none';
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Помилка при створенні запису');
        }
    } catch (error) {
        alert('Помилка: ' + error.message);
    }
}

// Перемикання видимості списку послуг
function toggleServices() {
    const servicesList = document.getElementById('servicesList');
    const button = document.querySelector('.dropdown-button');

    if (servicesList && button) {
        if (servicesList.classList.contains('hidden')) {
            servicesList.classList.remove('hidden');
            button.innerHTML = 'Послуги та вартість ▲';
        } else {
            servicesList.classList.add('hidden');
            button.innerHTML = 'Послуги та вартість ▼';
        }
    }
}

// Ініціалізація
document.addEventListener('DOMContentLoaded', function () {
    loadFormData(); // Завантажуємо дані лікарів і послуг

    // Додаємо обробник кнопки "Записатися на прийом"
    const appointmentBtn = document.querySelector('.appointment-btn');
    if (appointmentBtn) {
        appointmentBtn.addEventListener('click', function (e) {
            e.preventDefault();
            showAppointmentForm();
        });
    }
// Додаємо обробник відправки форми
const appointmentForm = document.querySelector('#appointmentForm');
if (appointmentForm && !appointmentForm.dataset.initialized) {
    appointmentForm.addEventListener('submit', submitAppointment);
    appointmentForm.dataset.initialized = true; // Уникнення повторного додавання
} })

