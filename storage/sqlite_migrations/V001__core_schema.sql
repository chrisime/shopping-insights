create table if not exists retailer
(
    code    text primary key,
    name    text not null,
    country text not null
);

create table if not exists store
(
    id            integer primary key autoincrement,
    retailer_code varchar not null,
    name          varchar not null,
    street        varchar not null,
    street_no     varchar not null,
    zip           varchar not null,
    city          varchar not null,
    hash          varchar not null,

    constraint fk_store__retailer
        foreign key (retailer_code) references retailer (code) on delete cascade,

    constraint uq_store__retailer_hash
        unique (hash)
);

create index if not exists idx_store__retailer_code
    on store (retailer_code);

create table if not exists purchase
(
    id            varchar primary key,
    store_id      integer,
    purchase_date date    not null,
    market        varchar,
    register_id   varchar,
    cashier       varchar,
    total_price   real,
    discount      real    not null default 0,
    saved_deposit real    not null default 0,
    currency      varchar not null default 'EUR',
    source_file   varchar,
    hash          varchar not null,

    constraint fk_purchase__store
        foreign key (store_id) references store (id) on delete cascade,

    constraint uq_purchase__hash
        unique (hash)
);

create index if not exists idx_purchase__store_id
    on purchase (store_id);

create table if not exists purchase_item
(
    id          integer primary key autoincrement,
    purchase_id varchar not null,
    position    integer not null,
    name        varchar not null,
    quantity    real    not null default 1,
    unit        varchar not null default 'stk',
    price       real    not null,

    constraint fk_purchase_item__purchase
        foreign key (purchase_id) references purchase (id) on delete cascade,

    constraint uq_purchase_item__purchase_position unique (purchase_id, position)
);

create table if not exists payment_method
(
    id          integer primary key autoincrement,
    purchase_id varchar not null,
    position    integer not null,
    method      varchar not null,
    network     varchar,
    amount      real,

    constraint fk_payment_method__purchase
        foreign key (purchase_id) references purchase (id) on delete cascade,

    constraint uq_payment_method__purchase_position unique (purchase_id, position)
);

create table if not exists purchase_lidl
(
    purchase_id       text primary key,
    lidlplus_discount real,
    sticker_discount  real,

    constraint fk_purchase_lidl__purchase
        foreign key (purchase_id) references purchase (id) on delete cascade
);

create table if not exists purchase_rewe
(
    purchase_id             text primary key,
    rewe_bonus_amount       real not null default 0,
    rewe_bonus_total_amount real not null default 0,
    rewe_bonus_discount     real not null default 0,

    constraint fk_purchase_rewe__purchase
        foreign key (purchase_id) references purchase (id) on delete cascade
);

-- Cascade DELETE triggers as fallback for tools that don't enable PRAGMA foreign_keys.

create trigger if not exists trg_store_delete_purchases
    after delete
    on store
    for each row
begin
    delete from purchase where store_id = old.id;
end;

create trigger if not exists trg_purchase_delete_items
    after delete
    on purchase
    for each row
begin
    delete from purchase_item where purchase_id = old.id;
end;

create trigger if not exists trg_purchase_delete_payments
    after delete
    on purchase
    for each row
begin
    delete from payment_method where purchase_id = old.id;
end;

create trigger if not exists trg_purchase_delete_lidl
    after delete
    on purchase
    for each row
begin
    delete from purchase_lidl where purchase_id = old.id;
end;

create trigger if not exists trg_purchase_delete_rewe
    after delete
    on purchase
    for each row
begin
    delete from purchase_rewe where purchase_id = old.id;
end;
