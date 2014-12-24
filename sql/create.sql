begin;
create table customer
(id integer PRIMARY KEY AUTOINCREMENT,
    acct varchar(12) NOT NULL UNIQUE,
    status varchar(1) NOT NULL CHECK(status = 'A' or status = 'I'),
    fn varchar(35) NOT NULL,
    ln varchar(35) NOT NULL,
    addr varchar(35) NOT NULL,
    city varchar(35) NOT NULL,
    state varchar(2) NOT NULL
);
create table pin
(id integer PRIMARY KEY AUTOINCREMENT,
    acct varchar(12) NOT NULL UNIQUE,
    pin varchar(4) NOT NULL,
    foreign key (acct) references customer(acct)
);
create table balance
(id integer PRIMARY KEY AUTOINCREMENT,
    acct varchar(12) NOT NULL,
    balance decimal(7,2) NOT NULL UNIQUE,
    foreign key (acct) references customer(acct)
);
create table trans
(id integer PRIMARY KEY AUTOINCREMENT,
    acct varchar(12) NOT NULL,
    tacct varchar(12) NULL,
    amount decimal(7,2) NOT NULL,
    trntype varchar(1) NOT NULL CHECK(trntype in ('D', 'W', 'T', 'X', 'P')),
    time_start datetime NOT NULL,
    time_end datetime,
    foreign key (acct) references customer(acct),
    foreign key (tacct) references customer(acct)
);
create table debst
(id integer PRIMARY KEY AUTOINCREMENT,
    acct varchar(12) NOT NULL,
    status varchar(1) NOT NULL CHECK(status = 'A' or status = 'I'),
    foreign key (acct) references customer(acct)
);
commit;
