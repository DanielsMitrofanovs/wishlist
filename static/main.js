$(document).ready(function() {
  $('.gift-card').on('click', function() {
    const giftTitle = $(this).find('.card-title').text();
    const giftDescription = $(this).find('.card-text').text();
    const giftLink = $(this).data('link');
    const giftPrice = $(this).data('price');

    $('#giftModal .modal-title').text(giftTitle);
    $('#giftModal .modal-body .description').text(giftDescription);
    $('#giftModal .modal-body .link').attr('href', giftLink).text(giftLink);
    $('#giftModal .modal-body .price').text(`Цена: ${giftPrice}€`);

    $('#giftModal').modal('show');
  });
});
