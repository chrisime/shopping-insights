pragma foreign_keys = off;

drop index if exists idx_purchase__source_hash;

create table if not exists purchase__new
(
    id            varchar primary key,
    store_id      integer,
    purchase_date date    not null,
    market        varchar,
    register_id   varchar,
    cashier       varchar,
    total_price   real,
    amount_saved  real    not null default 0,
    saved_deposit real    not null default 0,
    currency      varchar not null default 'EUR',
    source_file   varchar,
    hash          varchar not null,

    constraint fk_purchase__store
        foreign key (store_id) references store (id) on delete cascade,

    constraint uq_purchase__hash
        unique (hash)
);

insert into purchase__new (
    id,
    store_id,
    purchase_date,
    market,
    register_id,
    cashier,
    total_price,
    amount_saved,
    saved_deposit,
    currency,
    source_file,
    hash
)
select
    id,
    store_id,
    purchase_date,
    market,
    register_id,
    cashier,
    total_price,
    amount_saved,
    saved_deposit,
    currency,
    source_file,
    hash
from purchase;

drop table purchase;
alter table purchase__new rename to purchase;

create index if not exists idx_purchase__store_id
    on purchase (store_id);

pragma foreign_keys = on;

