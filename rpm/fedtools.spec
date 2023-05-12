%global package_name fedtools

Name:           python-%{package_name}
Version:        0.4.1
Release:        1%{?dist}
Summary:        CLI that make the life of a fedora packager easier

License:        MIT
URL:            https://github.com/blinxen/%{package_name}
Source:         %{url}/archive/%{version}/%{package_name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel

%global _description %{expand:
CLI that make the life of a fedora packager easier.}

%description %_description


%package -n %{package_name}
Summary:        %{summary}

%description -n %{package_name} %_description


%prep
%autosetup -n %{package_name}-%{version_no_tilde} -p1


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
install -D -p -m 0644 conf/fedtools.bash %{buildroot}/usr/share/bash-completion/completions/fedtools.bash


%check


%files -n %{package_name}
%doc README.md
%license LICENSE
/usr/share/bash-completion/completions/fedtools.bash
%{python3_sitelib}/%{package_name}/
%{python3_sitelib}/%{package_name}-%{version}.dist-info/
%{_bindir}/%{package_name}


%changelog
* Fri May 12 2023 blinxen <h-k-81@hotmail.com> - 0.4.1-1
- Update to version 0.4.1
- Fix wrongly matched package name in review subcommand
- More user friendly error message in review subcommand
* Wed May 10 2023 blinxen <h-k-81@hotmail.com> - 0.4.0-1
- Update to version 0.4.0
- Add copr-review subcommand with which the user can build srpm in copr and run
  fedora-review after. This is mostly used when reviewing packages.
* Wed Apr 26 2023 blinxen <h-k-81@hotmail.com> - 0.3.2-1
- Update to version 0.3.2
- Allow user to set path for fp-upload and check-versions
- Ignore version prefixes in check-versions

* Wed Apr 12 2023 blinxen <h-k-81@hotmail.com> - 0.3.1-2
- Add bash completion

* Wed Apr 12 2023 blinxen <h-k-81@hotmail.com> - 0.3.1-1
- Initial package
