-- Minimal seed for demo. The ML pipeline's push_to_supabase.py replaces this
-- with real data from the trained artifacts.
insert into teams (name, code, confederation) values
 ('Brazil','BRA','CONMEBOL'),
 ('Argentina','ARG','CONMEBOL'),
 ('France','FRA','UEFA'),
 ('Germany','GER','UEFA'),
 ('Spain','ESP','UEFA'),
 ('England','ENG','UEFA'),
 ('Portugal','POR','UEFA'),
 ('Netherlands','NED','UEFA'),
 ('Belgium','BEL','UEFA'),
 ('Croatia','CRO','UEFA'),
 ('Morocco','MAR','CAF'),
 ('Japan','JPN','AFC'),
 ('South Korea','KOR','AFC'),
 ('United States','USA','CONCACAF'),
 ('Mexico','MEX','CONCACAF'),
 ('Uruguay','URU','CONMEBOL')
on conflict (name) do nothing;
