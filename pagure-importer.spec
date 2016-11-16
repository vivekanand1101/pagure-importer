%global modname pgimport
%global sum Command line issues importer to pagure .

Name:           pagure-importer
Version:        2.0
Release:        1%{?dist}
Summary:        %{sum}

License:       GPLv2
URL:           https://pagure.io/pagure-importer
Source0:       https://pagure.io/releases/pagure-importer/pgimport-%{version}.tar.gz

BuildArch:     noarch

BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python3-github
BuildRequires: python3-pygit2
BuildRequires: python3-fedora
BuildRequires: python3-click
BuildRequires: python3-werkzeug

Requires: python3-github
Requires: python3-pygit2
Requires: python3-fedora
Requires: python3-click
Requires: python3-werkzeug
Requires: git-core

%description
pagure-importer is a command line tool to make easy the migration of issues from github
and fedorahosted to pagure

%package -n python3-%{modname}
Summary:        %{sum}
%{?python_provide:%python_provide python3-%{modname}}

%description -n python3-%{modname}
pagure-importer is a command line tool to make easy the migration of issues from github
and fedorahosted to pagure

%prep
%autosetup -n %{modname}-%{version}

rm -rf %{modname}.egg-info


%build
%py3_build

%install
%py3_install


%files -n python3-%{modname}
%license LICENSE
%doc README.md
%{python3_sitelib}/*
%{_bindir}/pgimport


%changelog
* Mon Nov 14 2016 Clement Verna <cverna@tutanota.com> - 1.2.3
- need to install RPMs as root form copr, so use sudo
- separate milestone and tags, better tags pre-processing
- custom fields for fedorahosted tickets
- Fix #68 'list' object has no attribute 'username' on pgimport github
- Get more than one attachment per comment
- Add Documentation to turn off Fedmsg hook and code refactor
- Strip trailling /
* Sun Oct 23 2016 Clement Verna <cverna@tutanota.com> - 1.2.2
- Add flag for pagure project which already have issues
- Add support for close status
- Try to get trac project milestone if exist, if not just carry on
- pagure now has 'Closed' instead of 'Fixed'
* Sat Oct 08 2016 Clement Verna <cverna@tutanota.com> - 1.2.1
- Some make up in our code
- Milestone support for github importer
- Let click handle the stdout
- Add two-factor authentication to Github importer
- Added tag to import all issues as private by default
- include enabling pagure tickets plugin instructions where all commands are placed to double sure
- tags command improvement
* Tue Sep 06 2016 Clement Verna <cverna@tutanota.com> - 1.2.0
- Reduce number of opened file by cloning and deleting only once the working repo
- Improve usage example documentation
- Change protocol used to get data from fedorahosted from XML-RPC to JSON-RPC

* Thu Aug 11 2016 Clement Verna <cverna@tutanota.com> - 1.1.0
- initial package for Fedora
