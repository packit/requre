%global srcname requre

Name:           python-%{srcname}
Version:        0.8.2
Release:        1%{?dist}
Summary:        Python library what allows re/store output of various objects for testing

License:        MIT
URL:            https://github.com/packit/requre
Source0:        %{pypi_source}
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3dist(click)
BuildRequires:  python3dist(pytest)
BuildRequires:  python3dist(pyyaml)
BuildRequires:  python3dist(requests)
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(setuptools-scm)
BuildRequires:  python3dist(sphinx)

%description
REQUest REcordingRequre [rekure] - Is Library for storing output of various
function and methods to persistent storage and be able to replay the stored
output to functions.

%package -n     python3-%{srcname}
Summary:        %{summary}

# https://docs.fedoraproject.org/en-US/packaging-guidelines/Python/#_provides
%if 0%{?fedora} < 33
%{?python_provide:%python_provide python3-%{srcname}}
%endif

%description -n python3-%{srcname}
REQUest REcordingRequre [rekure] - Is Library for storing output of various
function and methods to persistent storage and be able to replay the stored
output to functions.

%prep
%autosetup -n %{srcname}-%{version}
# Remove bundled egg-info
rm -rf %{srcname}.egg-info

%build
%py3_build

%install
%py3_install

%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{_bindir}/requre-patch
%{python3_sitelib}/%{srcname}
%{python3_sitelib}/%{srcname}-%{version}-py%{python3_version}.egg-info

%changelog
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
