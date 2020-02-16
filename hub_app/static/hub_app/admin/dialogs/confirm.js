(function ($, win) {

    $('a[data-confirm]').on('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        const confirmMessage = $(this).attr('data-confirm');
        if (self.confirm(confirmMessage)) {
            win.location.replace($(this).attr('href'));
        }
    });

})(jQuery, window);
