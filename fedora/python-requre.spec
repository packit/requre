%global desc %{expand:
REQUest REcordingRequre [rekure] - Is Library for storing output of various
function and methods to persistent storage and be able to replay the stored
output to functions.}


Name:           python-requre
Version:        0.9.1
Release:        1%{?dist}
Summary:        Python library that allows re/store output of various objects for testing

License:        MIT
URL:            https://github.com/packit/requre
Source0:        %{pypi_source requre}
BuildArch:      noarch

BuildRequires:  python3-devel


%description
%{desc}


%package -n     python3-requre
Summary:        %{summary}


%description -n python3-requre
%{desc}


%prep
%autosetup -n requre-%{version}


%generate_buildrequires
# The -w flag is required for EPEL 9's older hatchling
%pyproject_buildrequires %{?el9:-w}


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files requre


%files -n python3-requre -f %{pyproject_files}
# Epel9 does not tag the license file in pyproject_files as a license. Manually install it in this case
%if 0%{?el9}
%license LICENSE
%endif
%doc README.md
%{_bindir}/requre-patch


%changelog
* Fri Mar 21 2025 Packit Team <hello@packit.dev> - 0.9.1-1
- New upstream release 0.9.1

* Fri Feb 14 2025 Matej Focko <mfocko@redhat.com> - 0.9.0-1
- New upstream release 0.9.0

* Mon Feb 10 2025 Packit Team <hello@packit.dev> - 0.8.6-1
- New upstream release 0.8.6

* Fri Feb 07 2025 Packit Team <hello@packit.dev> - 0.8.5-1
- New upstream release 0.8.5

* Sun Jan 07 2024 Packit Team <hello@packit.dev> - 0.8.4-1
- New upstream release 0.8.4

* Mon Oct 30 2023 Packit Team <hello@packit.dev> - 0.8.3-1
- New upstream release 0.8.3

* Wed Apr 13 2022 Frantisek Lachman <flachman@redhat.com> - 0.8.2-1
- New upstream release 0.8.2

* Fri Jun 18 2021 Frantisek Lachman <flachman@redhat.com> - 0.8.1-1
- New upstream release 0.8.1

* Fri May 07 2021 Frantisek Lachman <flachman@redhat.com> - 0.8.0-1
- New upstream release 0.8.0

* Fri Apr 30 2021 Hunor Csomortáni <csomh@redhat.com> - 0.7.1-1
- New upstream release: 0.7.1

* Fri Mar 12 2021 Jan Ščotka <jscotka@redhat.com> - 0.7.0-1
- New version

* Mon Mar 01 2021 Jan Ščotka <jscotka@redhat.com> - 0.6.1-1
- new version

* Tue Feb 16 2021 Jan Ščotka <jscotka@redhat.com> - 0.6.0-1
- new version

* Tue Jan 19 2021 Jiri Popelka <jpopelka@redhat.com> - 0.5.0-1
- 0.5.0

* Tue Sep 22 2020 Jan Ščotka <jscotka@redhat.com> - 0.4.0-1
- New upstream release 0.4.0

* Wed Jan 15 2020 Jan Ščotka <jscotka@redhat.com> - 0.2.0-1
- Initial package.
