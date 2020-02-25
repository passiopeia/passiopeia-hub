(($) => {

    const putEventHandler = (event) => {
        const url = $(event.data).attr('data-put');
        const token = $(event.data).parent('form').find('input[name="csrfmiddlewaretoken"]').attr('value');
        $.ajax(url, {
            type: 'PUT',
            dataType: 'json',
            headers: {
                'X-PH-CSRF-TOKEN': token
            },
            success: (result) => {
                document.location.href = url;
            },
            error: (error) => {
                document.location.href = url;
            }
        });
    };

    $(document).ready(() => {
        $('button[data-put]').each((index, button) => {
            $(button).on('click', null, button, putEventHandler);
        });
    });

})(jQuery);