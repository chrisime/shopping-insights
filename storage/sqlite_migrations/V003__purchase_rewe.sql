create table if not exists purchase_rewe (
    purchase_id text primary key,
    rewe_bonus_amount real not null default 0,
    rewe_bonus_total_amount real not null default 0,
    rewe_bonus_amount_saved real not null default 0,
    constraint fk_purchase_rewe__purchase
        foreign key (purchase_id) references purchase(id) on delete cascade
);
