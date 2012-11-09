# -*- coding: utf-8 -*-
"""

    @author: Fabio Erculiani <lxnay@sabayon.org>
    @contact: lxnay@sabayon.org
    @copyright: Fabio Erculiani
    @license: GPL-2

    B{Entropy Command Line Client}.

"""
import os
import sys
import re
import argparse

from entropy.const import etpConst, const_convert_to_unicode, \
    const_convert_to_rawstring
from entropy.i18n import _, ngettext
from entropy.output import darkgreen, darkred, blue, teal, purple, brown, \
    bold

import entropy.tools

from solo.commands.descriptor import SoloCommandDescriptor
from solo.commands.command import SoloCommand
from solo.utils import print_package_info, print_table, get_file_mime, \
    graph_packages, revgraph_packages


class SoloQuery(SoloCommand):
    """
    Main Solo Query command.
    """

    NAME = "query"
    ALIASES = ["q"]
    ALLOW_UNPRIVILEGED = True

    INTRODUCTION = """\
Repository query tools.
"""
    SEE_ALSO = ""

    def __init__(self, args):
        SoloCommand.__init__(self, args)
        self._nsargs = None
        self._commands = {}

    def man(self):
        """
        Overridden from SoloCommand.
        """
        return self._man()

    def _get_parser(self):
        """
        Overridden from SoloCommand.
        """
        _commands = {}

        descriptor = SoloCommandDescriptor.obtain_descriptor(
            SoloQuery.NAME)
        parser = argparse.ArgumentParser(
            description=descriptor.get_description(),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog="%s %s" % (sys.argv[0], SoloQuery.NAME))

        self._setup_verbose_quiet_parser(parser)

        subparsers = parser.add_subparsers(
            title="action", description=_("repository query tools"),
            help=_("available commands"))

        belongs_parser = subparsers.add_parser(
            "belongs",
            help=_("resolve what package a file belongs to"))
        belongs_parser.add_argument(
            "files", nargs='+', metavar="<file>",
            help=_("file path"))
        self._setup_verbose_quiet_parser(belongs_parser)
        belongs_parser.set_defaults(func=self._belongs)
        _commands["belongs"] = {}

        changelog_parser = subparsers.add_parser(
            "changelog",
            help=_("show package changelog"))
        changelog_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        self._setup_verbose_quiet_parser(changelog_parser)
        changelog_parser.set_defaults(func=self._changelog)
        _commands["changelog"] = {}

        revdeps_parser = subparsers.add_parser(
            "revdeps",
            help=_("show reverse dependencies of package"))
        revdeps_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        self._setup_verbose_quiet_parser(revdeps_parser)
        revdeps_parser.set_defaults(func=self._revdeps)
        _commands["revdeps"] = {}

        desc_parser = subparsers.add_parser(
            "description",
            help=_("search package by description"))
        desc_parser.add_argument(
            "descriptions", nargs='+', metavar="<description>",
            help=_("description keyword"))
        desc_parser.set_defaults(func=self._description)
        self._setup_verbose_quiet_parser(desc_parser)
        _commands["description"] = {}

        files_parser = subparsers.add_parser(
            "files",
            help=_("show files owned by package"))
        files_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        files_parser.set_defaults(func=self._files)
        self._setup_verbose_quiet_parser(files_parser)
        _commands["files"] = {}

        installed_parser = subparsers.add_parser(
            "installed",
            help=_("search installed packages"))
        installed_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        installed_parser.set_defaults(func=self._installed)
        self._setup_verbose_quiet_parser(installed_parser)
        _commands["installed"] = {}

        lic_parser = subparsers.add_parser(
            "license",
            help=_("show packages using the given license"))
        lic_parser.add_argument(
            "licenses", nargs='+', metavar="<license>",
            help=_("license name"))
        lic_parser.set_defaults(func=self._license)
        self._setup_verbose_quiet_parser(lic_parser)
        _commands["license"] = {}

        list_parser = subparsers.add_parser(
            "list", help=_("list packages"))
        self._setup_verbose_quiet_parser(list_parser)
        list_d = {}
        _commands["list"] = list_d


        list_subparsers = list_parser.add_subparsers(
            title="action", description=_("list packages"),
            help=_("available commands"))

        installed_parser = list_subparsers.add_parser(
            "installed", help=_("list installed packages"))
        installed_parser.add_argument(
            "--by-user", action="store_true", default=False,
            help=_("only list packages installed by user"))
        installed_parser.add_argument(
            "repos", metavar="<repo>", nargs="*",
            help=_("only list packages installed from given repositories"))
        self._setup_verbose_quiet_parser(installed_parser)
        installed_parser.set_defaults(func=self._list_installed)
        list_d["installed"] = {
            "--by-user": {},
        }

        available_parser = list_subparsers.add_parser(
            "available", help=_("list available packages"))
        available_parser.add_argument(
            "repos", metavar="<repo>", nargs="+",
            help=_("only list packages from given repositories"))
        self._setup_verbose_quiet_parser(available_parser)
        available_parser.set_defaults(func=self._list_available)
        list_d["available"] = {}


        mime_parser = subparsers.add_parser(
            "mimetype",
            help=_("show packages able to handle the given mimetype"))
        mime_parser.add_argument(
            "mimes", nargs='+', metavar="<mime>",
            help=_("mimetype"))
        mime_parser.add_argument(
            "--installed", action="store_true", default=False,
            help=_("only show installed packages"))
        self._setup_verbose_quiet_parser(mime_parser)
        mime_parser.set_defaults(func=self._mimetype)
        _commands["mimetype"] = {
            "--installed": {},
        }

        associate_parser = subparsers.add_parser(
            "associate",
            help=_("associate file to packages able to handle it"))
        associate_parser.add_argument(
            "files", nargs='+', metavar="<file>",
            help=_("file path"))
        associate_parser.add_argument(
            "--installed", action="store_true", default=False,
            help=_("only show installed packages"))
        self._setup_verbose_quiet_parser(associate_parser)
        associate_parser.set_defaults(func=self._associate)
        _commands["associate"] = {
            "--installed": {},
        }

        needed_parser = subparsers.add_parser(
            "needed",
            help=_("show runtime libraries needed by the given package"))
        needed_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        self._setup_verbose_quiet_parser(needed_parser)
        needed_parser.set_defaults(func=self._needed)
        _commands["needed"] = {}

        orphans_parser = subparsers.add_parser(
            "orphans",
            help=_("search files not belonging to any packages"))
        orphans_parser.set_defaults(func=self._orphans)
        _commands["orphans"] = {}

        required_parser = subparsers.add_parser(
            "required",
            help=_("show packages requiring the given library name"))
        required_parser.add_argument(
            "libraries", nargs='+', metavar="<library>",
            help=_("library name (example: libdl.so.2)"))
        self._setup_verbose_quiet_parser(required_parser)
        required_parser.set_defaults(func=self._required)
        _commands["required"] = {}

        sets_parser = subparsers.add_parser(
            "sets",
            help=_("search package sets"))
        sets_parser.add_argument(
            "sets", nargs='*', metavar="<set>",
            help=_("set name"))
        self._setup_verbose_quiet_parser(sets_parser)
        sets_parser.set_defaults(func=self._sets)
        _commands["sets"] = {}

        slot_parser = subparsers.add_parser(
            "slot",
            help=_("show packages owning the given slot"))
        slot_parser.add_argument(
            "slots", nargs='+', metavar="<slot>",
            help=_("slot name"))
        self._setup_verbose_quiet_parser(slot_parser)
        slot_parser.set_defaults(func=self._slot)
        _commands["slot"] = {}

        tags_parser = subparsers.add_parser(
            "tags",
            help=_("show packages owning the given tag"))
        tags_parser.add_argument(
            "tags", nargs='+', metavar="<tag>",
            help=_("tag name"))
        self._setup_verbose_quiet_parser(tags_parser)
        tags_parser.set_defaults(func=self._tags)
        _commands["tags"] = {}

        revs_parser = subparsers.add_parser(
            "revisions",
            help=_("show packages at the given revision"))
        revs_parser.add_argument(
            "revisions", nargs='+', metavar="<revision>",
            help=_("revision name"))
        self._setup_verbose_quiet_parser(revs_parser)
        revs_parser.set_defaults(func=self._revisions)
        _commands["revisions"] = {}

        graph_parser = subparsers.add_parser(
            "graph",
            help=_("show the direct dependencies graph "
                   "for the given package"))
        graph_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        graph_parser.add_argument(
            "--complete", action="store_true", default=False,
            help=_("include system packages, build-time dependencies "
                   "and circular dependencies information"))
        self._setup_verbose_quiet_parser(graph_parser)
        graph_parser.set_defaults(func=self._graph)
        _commands["graph"] = {
            "--complete": {},
        }

        revgraph_parser = subparsers.add_parser(
            "revgraph",
            help=_("show the inverse dependencies graph "
                   "for the given package"))
        revgraph_parser.add_argument(
            "packages", nargs='+', metavar="<package>",
            help=_("package name"))
        revgraph_parser.add_argument(
            "--complete", action="store_true", default=False,
            help=_("include system packages, build-time dependencies "
                   "and circular dependencies information"))
        self._setup_verbose_quiet_parser(revgraph_parser)
        revgraph_parser.set_defaults(func=self._revgraph)
        _commands["revgraph"] = {
            "--complete": {},
        }


        self._commands = _commands
        return parser

    def parse(self):
        """
        Parse command
        """
        parser = self._get_parser()
        try:
            nsargs = parser.parse_args(self._args)
        except IOError as err:
            sys.stderr.write("%s\n" % (err,))
            return parser.print_help, []

        self._nsargs = nsargs
        return self._call_locked, [nsargs.func]

    def bashcomp(self, last_arg):
        """
        Overridden from SoloCommand.
        """
        self._get_parser() # this will generate self._commands
        outcome = ["--quiet", "-q", "--verbose", "-v"]
        return self._hierarchical_bashcomp(
            last_arg, outcome, self._commands)

    def _belongs(self, entropy_client):
        """
        Solo Query Belongs command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        files = self._nsargs.files
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Belong Search")),
                header=darkred(" @@ "))

        results = {}
        flatresults = {}
        reverse_symlink_map = entropy_client.Settings(
            )['system_rev_symlinks']

        for xfile in files:
            results[xfile] = set()
            pkg_ids = entropy_repository.searchBelongs(xfile)
            if not pkg_ids:
                # try real path if possible
                pkg_ids = entropy_repository.searchBelongs(
                    os.path.realpath(xfile))

            if not pkg_ids:
                # try using reverse symlink mapping
                for sym_dir in reverse_symlink_map:
                    if xfile.startswith(sym_dir):
                        for sym_child in reverse_symlink_map[sym_dir]:
                            my_file = sym_child+xfile[len(sym_dir):]
                            pkg_ids = entropy_repository.searchBelongs(
                                my_file)
                            if pkg_ids:
                                break

            for pkg_id in pkg_ids:
                if not flatresults.get(pkg_id):
                    results[xfile].add(pkg_id)
                    flatresults[pkg_id] = True

        if results:
            key_sorter = lambda x: entropy_repository.retrieveAtom(x)
            for result in results:

                # print info
                xfile = result
                result = results[result]

                for pkg_id in sorted(result, key = key_sorter):
                    if quiet:
                        entropy_client.output(
                            entropy_repository.retrieveAtom(pkg_id),
                            level="generic")
                    else:
                        print_package_info(pkg_id, entropy_client,
                            entropy_repository, installed_search = True,
                            extended = verbose, quiet = quiet)
                if not quiet:
                    toc = []
                    toc.append(("%s:" % (
                                blue(_("Keyword")),), purple(xfile)))
                    toc.append((
                            "%s:" % (
                                blue(_("Found")),), "%s %s" % (
                                len(result),
                                brown(ngettext("entry", "entries",
                                               len(result))),)))
                    print_table(entropy_client, toc)

        return 0

    def _changelog(self, entropy_client):
        """
        Solo Query Changelog command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        packages = self._nsargs.packages
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("ChangeLog Search")),
                header=darkred(" @@ "))

        for package in packages:
            repo = entropy_repository
            if entropy_repository is not None:
                pkg_id, rc = entropy_repository.atomMatch(package)
                if rc != 0:
                    entropy_client.output(
                        "%s: %s" % (
                            darkred(_("No match for")),
                            bold(package),))
                    continue
            else:
                pkg_id, r_id = entropy_client.atom_match(package)
                if pkg_id == -1:
                    entropy_client.output(
                        "%s: %s" % (
                            darkred(_("No match for")),
                            bold(package),))
                    continue
                repo = entropy_client.open_repository(r_id)

            repo_atom = repo.retrieveAtom(pkg_id)
            if quiet:
                entropy_client.output(
                    "%s :" % (repo_atom,),
                    level="generic")
            else:
                entropy_client.output(
                    "%s: %s" % (
                        blue(_("Package")),
                        bold(repo_atom),
                        ),
                    header=" "
                    )

            changelog = repo.retrieveChangelog(pkg_id)
            if not changelog or (changelog == "None"):
                # == "None" is a bug, see:
                # 685b865453d552d37ce3a9559f4cefb9a88f8beb
                entropy_client.output(
                    _("No ChangeLog available"),
                    level="generic")
            else:
                entropy_client.output(changelog, level="generic")
            entropy_client.output("=" * 80)

        if not quiet:
            # check developer repo mode
            repo_conf = entropy_client.Settings().get_setting_files_data(
                )['repositories']
            dev_repo = entropy_client.Settings(
                )['repositories']['developer_repo']
            if not dev_repo:
                entropy_client.output(
                    "%s ! [%s]" % (
                        brown(_("Attention: developer-repo "
                              "option not enabled")),
                        blue(repo_conf),
                    ),
                    level=bold(" !!! "))

        return 0

    def _revdeps(self, entropy_client):
        """
        Solo Query Revdeps command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        packages = self._nsargs.packages
        entropy_repository = entropy_client.installed_repository()
        settings = entropy_client.Settings()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Reverse Dependencies Search")),
                header=darkred(" @@ "))

        include_build_deps = False
        excluded_dep_types = None
        if include_build_deps:
            excluded_dep_types.append(
                etpConst['dependency_type_ids']['bdepend_id'])

        for package in packages:

            result = entropy_repository.atomMatch(package)
            match_in_repo = False
            repo_masked = False

            if result[0] == -1:
                match_in_repo = True
                result = entropy_client.atom_match(package)

            if result[0] == -1:
                result = entropy_client.atom_match(
                    package, mask_filter = False)
                if result[0] != -1:
                    repo_masked = True

            if result[0] != -1:

                repo = entropy_repository
                if match_in_repo:
                    repo = entropy_client.open_repository(result[1])
                key_sorter = lambda x: repo.retrieveAtom(x)

                found_atom = repo.retrieveAtom(result[0])
                if repo_masked:
                    package_id_masked, idmasking_reason = repo.maskFilter(
                        result[0])

                search_results = repo.retrieveReverseDependencies(
                    result[0], exclude_deptypes = excluded_dep_types)
                for pkg_id in sorted(search_results, key = key_sorter):
                    print_package_info(pkg_id, entropy_client, repo,
                        installed_search = True, strict_output = quiet,
                        extended = verbose, quiet = quiet)

                if not quiet:

                    masking_reason = ''
                    if repo_masked:
                        masking_reason = ", %s" % (
                            settings['pkg_masking_reasons'].get(
                                idmasking_reason),
                        )
                    repo_masked_str = const_convert_to_unicode(
                        repo_masked)
                    mask_str = bold(repo_masked_str) + masking_reason

                    toc = []
                    toc.append(("%s:" % (
                                blue(_("Keyword")),), purple(package)))
                    toc.append(("%s:" % (
                                blue(_("Matched")),), teal(found_atom)))
                    toc.append(("%s:" % (
                                blue(_("Masked")),), mask_str))

                    if match_in_repo:
                        where = "%s %s" % (
                            _("from repository"), result[1])
                    else:
                        where = _("from the installed packages repository")

                    entry_str = ngettext(
                        "entry", "entries", len(search_results))
                    toc.append(
                        ("%s:" % (blue(_("Found")),),
                         "%s %s %s" % (
                                len(search_results),
                                brown(entry_str),
                                where,)
                         ))
                    print_table(entropy_client, toc)

        return 0

    def _description(self, entropy_client):
        """
        Solo Query Description command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        descriptions = self._nsargs.descriptions
        entropy_repository = entropy_client.installed_repository()
        settings = entropy_client.Settings()

        found = False
        if not quiet:
            entropy_client.output(
                darkgreen(_("Description Search")),
                header=darkred(" @@ "))

        repo_number = 0
        for repo_id in entropy_client.repositories():
            repo_number += 1
            repo_data = settings['repositories']['available'][repo_id]

            if not quiet:
                header = const_convert_to_unicode("  #") + \
                    const_convert_to_unicode(repo_number) + \
                    const_convert_to_unicode(" ")
                entropy_client.output(
                    "%s" % (
                        bold(repo_data['description']),
                        ),
                    header=blue(header))

            repo = entropy_client.open_repository(repo_id)
            found = self._search_descriptions(
                descriptions, entropy_client, repo, quiet, verbose)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _search_descriptions(self, descriptions,
                             entropy_client, entropy_repository,
                             quiet, verbose):

        key_sorter = lambda x: entropy_repository.retrieveAtom(x)
        found = 0
        for desc in descriptions:

            pkg_ids = entropy_repository.searchDescription(
                desc, just_id = True)
            if not pkg_ids:
                continue

            found += len(pkg_ids)
            for pkg_id in sorted(pkg_ids, key = key_sorter):
                if quiet:
                    entropy_client.output(
                        entropy_repository.retrieveAtom(pkg_id))
                else:
                    print_package_info(
                        pkg_id, entropy_client,
                        entropy_repository,
                        extended = verbose, strict_output = False,
                        quiet = False)

            if not quiet:
                toc = []
                toc.append(("%s:" % (blue(_("Keyword")),), purple(desc)))
                toc.append(("%s:" % (blue(_("Found")),), "%s %s" % (
                    len(pkg_ids),
                    brown(ngettext("entry", "entries", len(pkg_ids))),)))
                print_table(entropy_client, toc)

        return found

    def _files(self, entropy_client):
        """
        Solo Query Files command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        packages = self._nsargs.packages
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Files Search")),
                header=darkred(" @@ "))

        for package in packages:

            pkg_id, pkg_rc = entropy_repository.atomMatch(package)
            if pkg_id == -1:
                continue

            atom = entropy_repository.retrieveAtom(pkg_id)
            files = entropy_repository.retrieveContentIter(
                pkg_id, order_by="file")
            files_len = 0
            if quiet:
                for xfile, ftype in files:
                    files_len += 1
                    entropy_client.output(xfile, level="generic")
            else:
                for xfile, ftype in files:
                    files_len += 1
                    entropy_client.output(
                        brown(xfile),
                        header=blue(" ### "))

            if not quiet:
                toc = []
                toc.append(("%s:" % (blue(_("Package")),), purple(atom)))
                toc.append(("%s:" % (blue(_("Found")),), "%s %s" % (
                    files_len, brown(_("files")),)))
                print_table(entropy_client, toc)

        return 0

    def _installed(self, entropy_client):
        """
        Solo Query Installed command.
        Alias of "solo search --installed".
        """
        from solo.commands.search import SoloSearch
        search = SoloSearch(
            self._nsargs, quiet=self._nsargs.quiet,
            verbose=self._nsargs.verbose,
            installed=True, packages=self._nsargs.packages)
        return search.search(entropy_client)

    def _license(self, entropy_client):
        """
        Solo Query License command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        licenses = self._nsargs.licenses
        settings = entropy_client.Settings()

        if not quiet:
            entropy_client.output(
                darkgreen(_("License Search")),
                header=darkred(" @@ "))

        found = False
        repo_number = 0
        for repo_id in entropy_client.repositories():
            repo_number += 1
            repo_data = settings['repositories']['available'][repo_id]

            if not quiet:
                header = const_convert_to_unicode("  #") + \
                    const_convert_to_unicode(repo_number) + \
                    const_convert_to_unicode(" ")
                entropy_client.output(
                    "%s" % (
                        bold(repo_data['description']),
                        ),
                    header=blue(header))

            repo = entropy_client.open_repository(repo_id)
            key_sorter = lambda x: repo.retrieveAtom(x)
            for mylicense in licenses:

                results = repo.searchLicense(mylicense, just_id = True)
                if not results:
                    continue

                found = True
                for pkg_id in sorted(results, key = key_sorter):
                    print_package_info(
                        pkg_id, entropy_client, repo,
                        extended = verbose,
                        strict_output = quiet,
                        quiet = quiet)

                if not quiet:
                    res_txt = ngettext("entry", "entries", len(results))
                    toc = []
                    toc.append(
                        ("%s:" % (blue(_("Keyword")),),
                         purple(mylicense)))
                    toc.append(
                        ("%s:" % (blue(_("Found")),),
                         "%s %s" % (len(results), brown(res_txt),)))

                    print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _list_packages(self, entropy_client, entropy_repository,
                       filter_funcs):
        """
        List packages in repository. The filter functions determine
        what packages shall be listed.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        settings = entropy_client.Settings()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Listing Packages")),
                header=darkred(" @@ "))

        repository_id = entropy_repository.repository_id()
        pkg_ids = entropy_repository.listAllPackageIds(
            order_by = "atom")
        for filter_func in filter_funcs:
            pkg_mtc = filter(
                filter_func,
                [(x, repository_id) for x in pkg_ids])
            pkg_ids = [x[0] for x in pkg_mtc]

        for pkg_id in pkg_ids:
            atom = entropy_repository.retrieveAtom(pkg_id)
            if atom is None:
                continue
            if not verbose:
                atom = entropy.dep.dep_getkey(atom)

            branchinfo = ""
            sizeinfo = ""
            if verbose:
                branch = entropy_repository.retrieveBranch(pkg_id)
                branchinfo = darkgreen(" [") + darkred(branch) + \
                    darkgreen("] ")
                mysize = entropy_repository.retrieveOnDiskSize(pkg_id)
                mysize = entropy.tools.bytes_into_human(mysize)
                sizeinfo = brown(" [") + purple(mysize) + brown("]")

            if not quiet:
                entropy_client.output(
                    "%s%s%s %s" % (
                        blue(const_convert_to_unicode(pkg_id)),
                        sizeinfo,
                        branchinfo,
                        atom),
                    header=darkred("# "))
            else:
                entropy_client.output(atom, level="generic")

        if not pkg_ids and not quiet:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _list_installed(self, entropy_client):
        """
        Solo Query List Installed command.
        """
        repositories = self._nsargs.repos
        by_user = self._nsargs.by_user

        def by_user_filter(pkg_match):
            pkg_id, pkg_repo = pkg_match
            repo_db = entropy_client.open_repository(pkg_repo)
            source_id = repo_db.getInstalledPackageSource(
                pkg_id)
            return source_id == etpConst['install_sources']['user']

        def by_repoid_filter(pkg_match):
            pkg_id, pkg_repo = pkg_match
            repo_db = entropy_client.open_repository(pkg_repo)
            inst_pkg_repo = repo_db.getInstalledPackageRepository(
                pkg_id)
            return inst_pkg_repo in repositories

        filter_funcs = []
        if by_user:
            filter_funcs.append(by_user_filter)
        if repositories:
            filter_funcs.append(by_repoid_filter)

        return self._list_packages(entropy_client,
            entropy_client.installed_repository(),
            filter_funcs)

    def _list_available(self, entropy_client):
        """
        Solo Query List Available command.
        """
        repositories = self._nsargs.repos
        quiet = self._nsargs.quiet
        entropy_repositories = entropy_client.repositories()
        exit_st = 1

        for repository_id in repositories:

            if repository_id not in entropy_repositories:
                if not quiet:
                    entropy_client.output(
                        "%s: %s" % (
                            teal(_("Repository is not available")),
                            repository_id,),
                        header=purple(" !!! "),
                        level="warning", importance=1)
                exit_st = 1
                break

            repo = entropy_client.open_repository(repository_id)
            exit_st = self._list_packages(entropy_client, repo, [])
            if exit_st != 0:
                break

        return exit_st

    def _search_mimetype(self, entropy_client, associate=False):
        """
        Solo Query Mimetype command.
        """
        installed = self._nsargs.installed
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        settings = entropy_client.Settings()
        inst_repo = entropy_client.installed_repository()
        inst_repo_id = inst_repo.repository_id()
        if associate:
            mimetypes = self._nsargs.files
        else:
            mimetypes = self._nsargs.mimes

        if not quiet:
            entropy_client.output(
                darkgreen(_("Searching Mimetype")),
                header=darkred(" @@ "))

        found = False
        for mimetype in mimetypes:

            if associate:
                # consider mimetype a file path
                mimetype = get_file_mime(mimetype)
                if mimetype is None:
                    continue

            if not quiet:
                entropy_client.output(
                    bold(mimetype),
                    header=blue("  # "))

            if installed:

                matches = [(x, inst_repo_id) for x in \
                    entropy_client.search_installed_mimetype(mimetype)]
            else:
                matches = entropy_client.search_available_mimetype(
                    mimetype)

            if matches:
                found = True

            key_sorter = lambda x: \
                entropy_client.open_repository(x[1]).retrieveAtom(x[0])
            for pkg_id, pkg_repo in sorted(matches, key = key_sorter):
                repo = entropy_client.open_repository(pkg_repo)
                print_package_info(pkg_id, entropy_client, repo,
                    extended = verbose, quiet = quiet)

            if not quiet:
                entry_str = ngettext("entry", "entries", len(matches))
                toc = []
                toc.append(("%s:" % (
                            blue(_("Keyword")),), purple(mimetype)))
                toc.append((
                        "%s:" % (blue(_("Found")),),
                        "%s %s" % (
                            len(matches),
                            brown(entry_str))
                        ))
                print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _mimetype(self, entropy_client):
        """
        Solo Query Mimetype command.
        """
        return self._search_mimetype(
            entropy_client,
            associate=False)

    def _associate(self, entropy_client):
        """
        Solo Query Associate command.
        """
        return self._search_mimetype(
            entropy_client,
            associate=True)

    def _needed(self, entropy_client):
        """
        Solo Query Needed command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        packages = self._nsargs.packages
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Needed Packages Search")),
                header=darkred(" @@ "))

        for package in packages:
            pkg_id, pkg_rc = entropy_repository.atomMatch(package)
            if pkg_id == -1:
                continue

            atom = entropy_repository.retrieveAtom(pkg_id)
            neededs = entropy_repository.retrieveNeeded(
                pkg_id, extended=True)
            for needed, elfclass in neededs:
                if verbose:
                    needed = "%s %s" % (needed, elfclass)
                if quiet:
                    entropy_client.output(
                        needed, level="generic")
                else:
                    entropy_client.output(
                        darkred(const_convert_to_unicode(needed)),
                        header=blue("  # "))
            if not quiet:
                toc = []
                toc.append(("%s:" % (blue(_("Package")),), purple(atom)))
                toc.append(("%s:" % (blue(_("Found")),), "%s %s" % (
                    len(neededs), brown(_("libraries")),)))
                print_table(entropy_client, toc)

        return 0

    def _orphans(self, entropy_client):
        """
        Solo Query Orphans command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        settings = entropy_client.Settings()
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Orphans Search")),
                header=darkred(" @@ "))

        reverse_symlink_map = settings['system_rev_symlinks']
        system_dirs_mask = [x for x in settings['system_dirs_mask'] \
            if entropy.tools.is_valid_path(x)]
        # make sure we're all rawstring.
        system_dirs_mask = [const_convert_to_rawstring(x) for x in \
                system_dirs_mask]

        system_dirs_mask_regexp = []
        for mask in settings['system_dirs_mask']:
            reg_mask = re.compile(mask)
            system_dirs_mask_regexp.append(reg_mask)

        file_data = set()
        dirs = settings['system_dirs']
        count = 0
        for xdir in dirs:
            # make sure it's bytes (raw encoding
            # as per EntropyRepository.retrieveContent())
            xdir = const_convert_to_rawstring(
                    xdir,
                    from_enctype=etpConst['conf_raw_encoding'])
            try:
                wd = os.walk(xdir)
            except RuntimeError: # maximum recursion?
                continue

            for currentdir, subdirs, files in wd:
                found_files = set()

                for filename in files:
                    filename = os.path.join(currentdir, filename)

                    # filter symlinks, broken ones will be reported
                    if os.path.islink(filename) and \
                            os.path.lexists(filename):
                        continue

                    do_cont = False
                    for mask in system_dirs_mask:
                        if filename.startswith(mask):
                            do_cont = True
                            break
                    if do_cont:
                        continue

                    for mask in system_dirs_mask_regexp:
                        if mask.match(filename):
                            do_cont = True
                            break

                    if do_cont:
                        continue

                    count += 1
                    filename_utf = const_convert_to_unicode(filename)
                    if not quiet and ((count == 0) or (count % 500 == 0)):
                        count = 0
                        if len(filename_utf) > 50:
                            fname = filename_utf[:40] + \
                                const_convert_to_unicode("...") + \
                                filename_utf[-10:]
                        else:
                            fname = filename_utf
                        entropy_client.output(
                            "%s: %s" % (
                                blue(_("Analyzing")),
                                fname),
                            header=darkred(" @@ "),
                            back=True)
                    found_files.add(filename_utf)

                if found_files:
                    file_data |= found_files

        totalfiles = len(file_data)

        if not quiet:
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Analyzed directories")),
                    " ".join(settings['system_dirs']),),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Masked directories")),
                    " ".join(settings['system_dirs_mask']),),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Number of files collected on the filesystem")),
                    bold(const_convert_to_unicode(totalfiles)),),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Now searching among installed packages")),
                    bold(const_convert_to_unicode(totalfiles)),),
                header=darkred(" @@ "))


        pkg_ids = entropy_repository.listAllPackageIds()
        length = str(len(pkg_ids))
        count = 0

        def gen_cont(pkg_id):
            for path, ftype in entropy_repository.retrieveContentIter(
                pkg_id):
                # reverse sym
                for sym_dir in reverse_symlink_map:
                    if path.startswith(sym_dir):
                        for sym_child in reverse_symlink_map[sym_dir]:
                            yield sym_child+path[len(sym_dir):]
                # real path also
                dirname_real = os.path.realpath(os.path.dirname(path))
                yield os.path.join(dirname_real, os.path.basename(path))
                yield path

        for pkg_id in pkg_ids:

            if not quiet:
                count += 1
                atom = entropy_repository.retrieveAtom(pkg_id)
                if atom is None:
                    continue
                entropy_client.output(
                    "%s: %s" % (
                        blue(_("Checking")),
                        bold(atom),),
                    header=darkred(" @@ "),
                    count=(count, length),
                    back=True)

            # remove from file_data
            file_data -= set(gen_cont(pkg_id))

        orphanedfiles = len(file_data)
        fname = "/tmp/entropy-orphans.txt"

        if not quiet:
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Number of total files")),
                    bold(const_convert_to_unicode(totalfiles))
                    ),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Number of matching files")),
                    bold(const_convert_to_unicode(
                            totalfiles - orphanedfiles))
                    ),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Number of orphaned files")),
                    bold(const_convert_to_unicode(orphanedfiles))
                    ),
                header=darkred(" @@ "))
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Writing file to disk")),
                    bold(const_convert_to_unicode(fname))
                    ),
                header=darkred(" @@ "))

        sizecount = 0
        file_data = list(file_data)
        file_data.sort(reverse = True)

        with open(fname, "wb") as f_out:

            for myfile in file_data:
                myfile = const_convert_to_rawstring(myfile)
                mysize = 0
                try:
                    mysize += os.stat(myfile).st_size
                except OSError:
                    mysize = 0
                sizecount += mysize

                f_out.write(myfile + const_convert_to_rawstring("\n"))
                if quiet:
                    entropy_client.output(myfile, level="generic")

            f_out.flush()

        humansize = entropy.tools.bytes_into_human(sizecount)
        if not quiet:
            entropy_client.output(
                "%s: %s" % (
                    blue(_("Total space wasted")),
                    bold(humansize)),
                header=darkred(" @@ "))
        else:
            entropy_client.output(humansize, level="generic")
        return 0

    def _required(self, entropy_client):
        """
        Solo Query Required command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        libraries = self._nsargs.libraries
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Required Packages Search")),
                header=darkred(" @@ "))

        key_sorter = lambda x: entropy_repository.retrieveAtom(x)
        for library in libraries:
            results = entropy_repository.searchNeeded(
                library, like = True)

            for pkg_id in sorted(results, key = key_sorter):
                print_package_info(
                    pkg_id, entropy_client, entropy_repository,
                    installed_search=True, strict_output=True,
                    extended=verbose, quiet=quiet)

            if not quiet:
                toc = []
                entity_str = ngettext("package", "packages", len(results))
                toc.append((
                        "%s:" % (blue(_("Library")),),
                        purple(library)))
                toc.append((
                        "%s:" % (
                            blue(_("Found")),),
                        "%s %s" % (
                            len(results),
                            brown(entity_str),)))
                print_table(entropy_client, toc)

        return 0

    def _sets(self, entropy_client):
        """
        Solo Query Sets command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        items = self._nsargs.sets
        if not items:
            items.append("*")

        if not quiet:
            entropy_client.output(
                darkgreen(_("Package Set Search")),
                header=darkred(" @@ "))

        sets = entropy_client.Sets()

        count = 0
        found = False
        for item in items:
            results = sets.search(item)
            key_sorter = lambda x: x[1]
            for repo, set_name, set_data in sorted(
                results, key = key_sorter):
                count += 1
                found = True

                if not quiet:
                    entropy_client.output(
                        bold(set_name),
                        header=blue("  #%d " % (count,)))

                    elements = sorted(set_data)
                    for element in elements:
                        entropy_client.output(
                            brown(element),
                            header="    ")
                else:
                    for element in sorted(set_data):
                        entropy_client.output(
                            element, level="generic")

            if not quiet:
                toc = []
                entity_str = ngettext("entry", "entries", count)
                toc.append(("%s:" % (blue(_("Keyword")),), purple(item)))
                toc.append(("%s:" % (blue(_("Found")),), "%s %s" % (
                    count, brown(entity_str),)))
                print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _slot(self, entropy_client):
        """
        Solo Query Slot command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        slots = self._nsargs.slots
        settings = entropy_client.Settings()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Slot Search")),
                header=darkred(" @@ "))

        found = False
        # search inside each available database
        repo_number = 0

        for repo_id in entropy_client.repositories():
            repo_number += 1
            repo_data = settings['repositories']['available'][repo_id]

            if not quiet:
                header = const_convert_to_unicode("  #") + \
                    const_convert_to_unicode(repo_number) + \
                    const_convert_to_unicode(" ")
                entropy_client.output(
                    "%s" % (
                        bold(repo_data['description']),
                        ),
                    header=blue(header))

            repo = entropy_client.open_repository(repo_id)
            for slot in slots:

                results = repo.searchSlotted(slot, just_id = True)
                key_sorter = lambda x: repo.retrieveAtom(x)
                for pkg_id in sorted(results, key = key_sorter):
                    found = True
                    print_package_info(pkg_id, entropy_client, repo,
                        extended=verbose, strict_output=quiet,
                        quiet=quiet)

                if not quiet:
                    toc = []
                    entity_str = ngettext("entry", "entries", len(results))
                    toc.append((
                            "%s:" % (blue(_("Keyword")),),
                            purple(slot)))
                    toc.append((
                            "%s:" % (blue(_("Found")),),
                            "%s %s" % (
                                len(results),
                                brown(entity_str),)))
                    print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))

        return 0

    def _tags(self, entropy_client):
        """
        Solo Query Tags command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        tags = self._nsargs.tags
        settings = entropy_client.Settings()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Tag Search")),
                header=darkred(" @@ "))

        found = False
        # search inside each available database
        repo_number = 0

        for repo_id in entropy_client.repositories():
            repo_number += 1
            repo_data = settings['repositories']['available'][repo_id]

            if not quiet:
                header = const_convert_to_unicode("  #") + \
                    const_convert_to_unicode(repo_number) + \
                    const_convert_to_unicode(" ")
                entropy_client.output(
                    "%s" % (
                        bold(repo_data['description']),
                        ),
                    header=blue(header))

            repo = entropy_client.open_repository(repo_id)
            for tag in tags:

                results = repo.searchTaggedPackages(tag)
                key_sorter = lambda x: repo.retrieveAtom(x)
                for pkg_id in sorted(results, key = key_sorter):
                    found = True
                    print_package_info(pkg_id, entropy_client, repo,
                        extended=verbose, strict_output=quiet,
                        quiet=quiet)

                if not quiet:
                    toc = []
                    entity_str = ngettext("entry", "entries", len(results))
                    toc.append((
                            "%s:" % (blue(_("Keyword")),),
                            purple(tag)))
                    toc.append((
                            "%s:" % (blue(_("Found")),),
                            "%s %s" % (
                                len(results),
                                brown(entity_str),)))
                    print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))
        return 0

    def _revisions(self, entropy_client):
        """
        Solo Query Revisions command.
        """
        quiet = self._nsargs.quiet
        verbose = self._nsargs.verbose
        revisions = self._nsargs.revisions
        settings = entropy_client.Settings()
        entropy_repository = entropy_client.installed_repository()

        if not quiet:
            entropy_client.output(
                darkgreen(_("Revision Search")),
                header=darkred(" @@ "))

        found = False
        key_sorter = lambda x: entropy_repository.retrieveAtom(x)

        for revision in revisions:
            results = entropy_repository.searchRevisionedPackages(
                revision)

            found = True
            for pkg_id in sorted(results, key = key_sorter):
                print_package_info(
                    pkg_id, entropy_client, entropy_repository,
                    extended=verbose, strict_output=quiet,
                    installed_search=True, quiet=quiet)

            if not quiet:
                toc = []
                entity_str = ngettext("entry", "entries", len(results))
                toc.append((
                        "%s:" % (blue(_("Keyword")),),
                        purple(revision)))
                toc.append((
                        "%s:" % (blue(_("Found")),),
                        "%s %s" % (
                            len(results),
                            brown(entity_str),)))
                print_table(entropy_client, toc)

        if not quiet and not found:
            entropy_client.output(
                darkgreen("%s." % (_("No matches"),)),
                header=darkred(" @@ "))
        return 0

    def _graph(self, entropy_client):
        """
        Solo Query Graph command.
        """
        packages = self._nsargs.packages
        quiet = self._nsargs.quiet
        complete = self._nsargs.complete

        return graph_packages(
            packages, entropy_client,
            complete=complete, quiet=quiet)

    def _revgraph(self, entropy_client):
        """
        Solo Query Revgraph command.
        """
        packages = self._nsargs.packages
        quiet = self._nsargs.quiet
        complete = self._nsargs.complete

        return revgraph_packages(
            packages, entropy_client,
            complete=complete, quiet=quiet)


SoloCommandDescriptor.register(
    SoloCommandDescriptor(
        SoloQuery,
        SoloQuery.NAME,
        _("repository query tools"))
    )
