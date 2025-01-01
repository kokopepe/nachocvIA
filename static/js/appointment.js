document.addEventListener('DOMContentLoaded', function() {
    const appointmentForm = document.getElementById('appointment-form');
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    const localTimezoneSpan = document.getElementById('local-timezone');
    const submitButton = document.getElementById('submit-btn');
    const selectedTimeInput = document.getElementById('selected-time');
    const dateInput = document.getElementById('date');
    const timezoneInput = document.getElementById('timezone');

    // Detect and display user's timezone
    const userTimezone = moment.tz.guess();
    localTimezoneSpan.textContent = userTimezone;
    timezoneInput.value = userTimezone;

    // Initialize FullCalendar
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        slotMinTime: '09:00:00',
        slotMaxTime: '18:00:00',
        allDaySlot: false,
        slotDuration: '00:30:00',
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true,
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5], // Monday - Friday
            startTime: '09:00',
            endTime: '18:00',
        },
        selectConstraint: 'businessHours',
        select: function(info) {
            const startTime = moment(info.start);
            const endTime = moment(info.end);

            // Format the selected time range for display
            const formattedTime = `${startTime.format('dddd, MMMM D, YYYY h:mm A')} - ${endTime.format('h:mm A')} (${userTimezone})`;
            selectedTimeInput.value = formattedTime;
            dateInput.value = startTime.toISOString();

            // Enable submit button
            submitButton.disabled = false;

            calendar.unselect();
        },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridWeek,timeGridDay'
        },
        events: function(info, successCallback, failureCallback) {
            // Fetch existing appointments from the server
            fetch('/appointment/slots')
                .then(response => response.json())
                .then(data => {
                    // Convert appointments to FullCalendar events
                    const events = data.appointments.map(apt => ({
                        start: apt.date,
                        end: moment(apt.date).add(30, 'minutes').toISOString(),
                        title: 'Booked',
                        color: 'red',
                        display: 'background'
                    }));
                    successCallback(events);
                })
                .catch(error => {
                    console.error('Error fetching appointments:', error);
                    failureCallback(error);
                });
        }
    });

    calendar.render();

    appointmentForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(appointmentForm);

        try {
            const response = await fetch('/appointment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(Object.fromEntries(formData))
            });

            const result = await response.json();
            if (result.success) {
                successModal.show();
                appointmentForm.reset();
                calendar.refetchEvents();
                submitButton.disabled = true;
                selectedTimeInput.value = '';
            } else {
                alert(result.error || 'Error booking appointment. Please try again.');
            }
        } catch (error) {
            alert('Error submitting appointment request. Please try again.');
        }
    });

    // Update calendar view on window resize
    window.addEventListener('resize', () => {
        calendar.updateSize();
    });

    // Set minimum date to today
    const today = new Date();
    const minDateTime = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Add 24 hours
    dateInput.min = minDateTime.toISOString().slice(0, 16);
});