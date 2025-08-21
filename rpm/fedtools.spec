Name:           fedtools
Version:        0.14.2
Release:        1%{?dist}
Summary:        CLI that make the life of a fedora packager easier

License:        MIT
URL:            https://github.com/blinxen/%{name}
Source:         %{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-rpm

Requires:  python3-rpm


%description
CLI that make the life of a fedora packager easier.


%prep
%autosetup -p1


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files -L fedtools
install -D -p -m 0644 conf/fedtools.bash %{buildroot}%{bash_completions_dir}/fedtools.bash


%check


%files -f %{pyproject_files}
%doc README.md
%license LICENSE
%{bash_completions_dir}/fedtools.bash
%{_bindir}/%{name}


%changelog
* Thu Aug 21 2025 blinxen <h-k-81@hotmail.com> - 0.14.2-1
- Update to version 0.14.2
* Sat Dec 21 2024 blinxen <h-k-81@hotmail.com> - 0.14.1-1
- Update to version 0.14.1
* Fri Nov 1 2024 blinxen <h-k-81@hotmail.com> - 0.14.0-1
- Update to version 0.14.0
* Sat Sep 21 2024 blinxen <h-k-81@hotmail.com> - 0.13.0-1
- Update to version 0.13.0
* Wed May 29 2024 blinxen <h-k-81@hotmail.com> - 0.12.0-1
- Update to version 0.12.0
* Sun May 05 2024 blinxen <h-k-81@hotmail.com> - 0.11.1-1
- Update to version 0.11.1
* Mon Jan 29 2024 blinxen <h-k-81@hotmail.com> - 0.11.0-1
- Update to version 0.11.0
* Sat Jan 20 2024 blinxen <h-k-81@hotmail.com> - 0.10.2-1
- Update to version 0.10.2
* Fri Jan 19 2024 blinxen <h-k-81@hotmail.com> - 0.10.1-1
- Update to version 0.10.1
* Mon Jan 15 2024 blinxen <h-k-81@hotmail.com> - 0.10.0-1
- Update to version 0.10.0
* Thu Nov 23 2023 blinxen <h-k-81@hotmail.com> - 0.9.2-1
- Update to version 0.9.2
* Thu Nov 02 2023 blinxen <h-k-81@hotmail.com> - 0.9.1-1
- Update to version 0.9.1
* Wed Nov 01 2023 blinxen <h-k-81@hotmail.com> - 0.9.0-1
- Update to version 0.9.0
* Tue Oct 31 2023 blinxen <h-k-81@hotmail.com> - 0.8.1-1
- Update to version 0.8.1
* Sun Oct 22 2023 blinxen <h-k-81@hotmail.com> - 0.8.0-1
- Update to version 0.8.0
- Rename subcommand "build" to "build-srpm"
- Update / fix code documentation
- Update / fix help messages
- Change configuration format from JSON to TOML
- Add new configuration option for users to specifc version prefixes in "check-versions" subcommand
* Thu Oct 05 2023 blinxen <h-k-81@hotmail.com> - 0.7.3-1
- Update to version 0.7.3
* Sat Sep 23 2023 blinxen <h-k-81@hotmail.com> - 0.7.2-1
- Update to version 0.7.2
* Sat Sep 16 2023 blinxen <h-k-81@hotmail.com> - 0.7.1-1
- Update to version 0.7.1
- Add f39 to copr chroots in copr review command
* Mon Jun 26 2023 blinxen <h-k-81@hotmail.com> - 0.7.0-1
- Update to version 0.7.0
* Sat Jun 24 2023 blinxen <h-k-81@hotmail.com> - 0.6.1-1
- Update to version 0.6.1
- Allow user to specify chroot in copr-review
* Sat Jun 24 2023 blinxen <h-k-81@hotmail.com> - 0.6.0-1
- Update to version 0.6.0
- Add new subcommand post-rust-review
* Tue Jun 13 2023 blinxen <h-k-81@hotmail.com> - 0.5.1-1
- Update to version 0.5.1
- Fix TYPO in build SRPM subcommand
* Wed Jun 07 2023 blinxen <h-k-81@hotmail.com> - 0.5.0-1
- Update to version 0.5.0
- Code improvements (no changes to the user)
- Improve regex used in review subcommand
* Sun May 28 2023 blinxen <h-k-81@hotmail.com> - 0.4.2-1
- Update to version 0.4.2
- Print URLs of the uploaded files in fp-upload subcommand
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
