
document.addEventListener('DOMContentLoaded', function() {
    // Handle book meeting link clicks
    document.querySelectorAll('a[href="/appointment"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            Cal("ui", {
                calLink: "jacobo-s.-carballada-vbmhib/30min",
                element: "#cal-booking-modal",
                layout: "month_view"
            });
            document.getElementById('cal-booking-modal').style.display = 'block';
        });
    });

    // Contact form handling
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(contactForm);
            
            try {
                const response = await fetch('/contact', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Message sent successfully!');
                    contactForm.reset();
                }
            } catch (error) {
                alert('Error sending message. Please try again.');
            }
        });
    }
});
