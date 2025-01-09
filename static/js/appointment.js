document.addEventListener('DOMContentLoaded', function() {
    const appointmentForm = document.getElementById('appointment-form');
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    const localTimezoneSpan = document.getElementById('local-timezone');
    const submitButton = document.getElementById('submit-btn');
    const selectedTimeInput = document.getElementById('selected-time'); //This will likely become obsolete
    const dateInput = document.getElementById('date'); //This will likely become obsolete
    const timezoneInput = document.getElementById('timezone');


    // Detect and display user's timezone
    const userTimezone = moment.tz.guess();
    localTimezoneSpan.textContent = userTimezone;
    timezoneInput.value = userTimezone;


    // Cal.com handles the scheduling functionality
    console.log('Calendar initialized');


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
                // calendar.refetchEvents(); - Removed as calendar is no longer used
                submitButton.disabled = true;
                selectedTimeInput.value = '';
            } else {
                alert(result.error || 'Error booking appointment. Please try again.');
            }
        } catch (error) {
            alert('Error submitting appointment request. Please try again.');
        }
    });

    // Removed FullCalendar related code and event listeners.

    // Set minimum date to today
    const today = new Date();
    const minDateTime = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Add 24 hours
    dateInput.min = minDateTime.toISOString().slice(0, 16);
});