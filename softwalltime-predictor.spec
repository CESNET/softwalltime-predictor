Name:    softwalltime-predictor
Version: 1.0
Release: 4
Summary: softwalltime-predictor
BuildRequires: python3
Requires: python3
Requires: python3-psycopg2

License: Public Domain
Source0: softwalltime-predictor-%{version}.tar.gz

%define debug_packages %{nil}
%define debug_package %{nil} 

%description
softwalltime-predictor

%prep
%setup

%build

%install
install -D -m 644 hook_softwalltime_predictor.py %{buildroot}/opt/pbs/hooks/hook_softwalltime_predictor.py
install -D -m 644 pbs_softwalltime_predictor %{buildroot}/etc/cron.d/pbs_softwalltime_predictor
install -D -m 644 softwalltime.conf %{buildroot}/opt/pbs/etc/softwalltime.conf
install -D -m 744 softwalltime_predictor-detector %{buildroot}/opt/pbs/bin/softwalltime_predictor-detector
install -D -m 744 softwalltime_predictor-runtime_saver %{buildroot}/opt/pbs/bin/softwalltime_predictor-runtime_saver
install -D -m 644 softwalltime_psql.py %{buildroot}/opt/pbs/lib/softwalltime/softwalltime_psql.py

%post
systemctl reload crond

%preun

%postun
systemctl reload crond

%files
/opt/pbs/hooks/hook_softwalltime_predictor.py
/etc/cron.d/pbs_softwalltime_predictor
%config /opt/pbs/etc/softwalltime.conf
/opt/pbs/bin/softwalltime_predictor-detector
/opt/pbs/bin/softwalltime_predictor-runtime_saver
/opt/pbs/lib/softwalltime/softwalltime_psql.py
%exclude /opt/pbs/hooks/hook_softwalltime_predictor.pyc
%exclude /opt/pbs/hooks/hook_softwalltime_predictor.pyo
%exclude /opt/pbs/lib/softwalltime/softwalltime_psql.pyc
%exclude /opt/pbs/lib/softwalltime/softwalltime_psql.pyo
%changelog
