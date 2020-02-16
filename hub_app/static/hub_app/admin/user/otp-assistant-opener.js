(function ($) {
    $('a[data-assistant-id="otp-assistant"]').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        const match = (document.location.pathname).match(/\/(\d+)\//);
        const url = $(this).attr('href').replace('0000000000000000', match[1]);
        const features = 'height=600,width=900,centerscreen=yes,menubar=no,toolbar=no,location=no,personalbar=no,status=no,resizable=yes,scrollbars=yes,chrome=yes,dialog=yes,modal=yes';
        window.open(url, 'otpAssistant', features, true);
    });
})(django.jQuery);
