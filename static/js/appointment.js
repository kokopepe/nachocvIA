document.addEventListener('DOMContentLoaded', function() {
    const appointmentForm = document.getElementById('appointment-form');
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    
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
            } else {
                alert(result.error || 'Error booking appointment. Please try again.');
            }
        } catch (error) {
            alert('Error submitting appointment request. Please try again.');
        }
    });
    
    // Set minimum date to today
    const dateInput = document.getElementById('date');
    const today = new Date();
    const minDateTime = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Add 24 hours
    dateInput.min = minDateTime.toISOString().slice(0, 16);
});
