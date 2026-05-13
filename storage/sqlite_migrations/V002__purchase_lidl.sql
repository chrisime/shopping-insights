create table if not exists purchase_lidl (
    purchase_id text primary key,
    lidlplus_amount_saved real,
    sticker_discount_amount real,
    constraint fk_purchase_lidl__purchase
        foreign key (purchase_id) references purchase(id) on delete cascade
);
