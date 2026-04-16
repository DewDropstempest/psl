# -*- coding: utf-8 -*-
#
# Copyright 2014 ko-zu <causeless@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import re
import unittest

from publicsuffixlist import PublicSuffixList, b, decode_idn, encode_idn, u

def bytestuple(x):
    return tuple(bytes(x).split(b'.'))


class TestPSL(unittest.TestCase):

    def setUp(self):

        self.psl = PublicSuffixList()

    def test_typesafe(self):
        self.assertEqual(self.psl.suffix("www.example.co.jp").__class__, "example.co.jp".__class__)
        self.assertEqual(self.psl.suffix(u("www.example.co.jp")).__class__, u("example.co.jp").__class__)

        self.assertEqual(self.psl.publicsuffix("www.example.co.jp").__class__, "co.jp".__class__)
        self.assertEqual(self.psl.publicsuffix(u("www.example.co.jp")).__class__, u("co.jp").__class__)

    def test_typesafe_bytestuple(self):
        self.assertEqual(
                self.psl.privatesuffix((b"www",b"example",b"co",b"jp")).__class__,
                (b"example", b"co", b"jp").__class__)
        self.assertEqual(
                self.psl.publicsuffix((b"www",b"example",b"co",b"jp")).__class__,
                (b"co", b"jp").__class__)
        self.assertEqual(
                self.psl.privatesuffix((b"www",b"example",b"co",b"jp"))[-1].__class__,
                (b"example", b"co", b"jp")[-1].__class__)
        self.assertEqual(
                self.psl.publicsuffix((b"www",b"example",b"co",b"jp"))[-1].__class__,
                (b"co", b"jp")[-1].__class__)

    def test_uppercase(self):
        self.assertEqual(self.psl.suffix("Jp"), None)
        self.assertEqual(self.psl.suffix("cO.Jp"), None)
        self.assertEqual(self.psl.suffix("eXaMpLe.cO.Jp"), "example.co.jp")
        self.assertEqual(self.psl.suffix("wWw.eXaMpLe.cO.Jp"), "example.co.jp")
        self.assertEqual(self.psl.publicsuffix("Jp"), "jp")
        self.assertEqual(self.psl.publicsuffix("cO.Jp"), "co.jp")
        self.assertEqual(self.psl.publicsuffix("eXaMpLe.cO.Jp"), "co.jp")
        self.assertEqual(self.psl.publicsuffix("wWw.eXaMpLe.cO.Jp"), "co.jp")

    def test_keepcase(self):
        self.assertEqual(self.psl.suffix("Jp", keep_case=True), None)
        self.assertEqual(self.psl.suffix("cO.Jp", keep_case=True), None)
        self.assertEqual(self.psl.suffix("eXaMpLe.cO.Jp", keep_case=True), "eXaMpLe.cO.Jp")
        self.assertEqual(self.psl.suffix("wWw.eXaMpLe.cO.Jp", keep_case=True), "eXaMpLe.cO.Jp")
        self.assertEqual(self.psl.publicsuffix("Jp", keep_case=True), "Jp")
        self.assertEqual(self.psl.publicsuffix("cO.Jp", keep_case=True), "cO.Jp")
        self.assertEqual(self.psl.publicsuffix("eXaMpLe.cO.Jp", keep_case=True), "cO.Jp")
        self.assertEqual(self.psl.publicsuffix("wWw.eXaMpLe.cO.Jp", keep_case=True), "cO.Jp")

    def test_notpermitted_domain(self):
        # From the PSL definition, empty labels are not permitted.
        # From the test_psl.txt, a leading dot is not permitted.
        # However, it seems most implementations ignore the trailing dot.

        self.assertEqual(self.psl.suffix(".example.com"), None)
        self.assertEqual(self.psl.publicsuffix(".example.com"), None)

        self.assertEqual(self.psl.suffix("www..invalid"), None)
        self.assertEqual(self.psl.suffix(""), None)
        self.assertEqual(self.psl.publicsuffix("www..invalid"), None)
        self.assertEqual(self.psl.publicsuffix(""), None)

    def test_ignored_trailing_dot(self):
        self.assertEqual(self.psl.suffix("example.com."), "example.com")
        self.assertEqual(self.psl.publicsuffix("example.com."), "com")

    def test_wiki_example(self):
        # from PSL Wiki
        # https://github.com/publicsuffix/list/wiki/Format/ffd14e41e850c69222eecf0aab4248619b53905a
        # https://github.com/publicsuffix/list/issues/1890
        source = """
com
*.foo.com
*.jp
*.hokkaido.jp
*.tokyo.jp
!pref.hokkaido.jp
!metro.tokyo.jp
"""
        psl = PublicSuffixList(source.splitlines())

        # According to the linter, this rule is incorrect
        # self.assertEqual(psl.is_private("foo.com"), True)
        self.assertEqual(psl.is_private("bar.foo.com"), False)
        self.assertEqual(psl.is_private("example.bar.foo.com"), True)
        self.assertEqual(psl.is_private("foo.bar.jp"), True)
        self.assertEqual(psl.is_private("bar.jp"), False)
        self.assertEqual(psl.is_private("foo.bar.hokkaido.jp"), True)
        self.assertEqual(psl.is_private("bar.hokkaido.jp"), False)
        self.assertEqual(psl.is_private("foo.bar.tokyo.jp"), True)
        self.assertEqual(psl.is_private("bar.tokyo.jp"), False)
        self.assertEqual(psl.is_private("pref.hokkaido.jp"), True)
        self.assertEqual(psl.is_private("metro.tokyo.jp"), True)

    def test_idn(self):
        tld = u("香港")
        self.assertEqual(self.psl.suffix(u("www.example.") + tld), u("example.") + tld)
        self.assertEqual(self.psl.publicsuffix(u("www.example.") + tld), tld)

    def test_punycoded(self):
        tld = encode_idn(u("香港"))
        self.assertEqual(self.psl.suffix(u("www.example.") + tld), u("example.") + tld)
        self.assertEqual(self.psl.publicsuffix(u("www.example.") + tld), tld)

    def test_suffix_deny_public(self):
        self.assertEqual(self.psl.suffix("com"), None)
        self.assertEqual(self.psl.suffix("co.jp"), None)
        self.assertEqual(self.psl.suffix("example.nagoya.jp"), None)

    def test_unknown(self):
        self.assertEqual(self.psl.suffix("www.example.unknowntld"), "example.unknowntld")
        self.assertEqual(self.psl.suffix("unknowntld"), None)

        self.assertEqual(self.psl.suffix("www.example.unknowntld", accept_unknown=True), "example.unknowntld")
        self.assertEqual(self.psl.suffix("unknowntld", accept_unknown=True), None)
        self.assertEqual(self.psl.suffix("www.example.unknowntld", accept_unknown=False), None)
        self.assertEqual(self.psl.suffix("unknowntld", accept_unknown=False), None)

        self.assertEqual(self.psl.publicsuffix("www.example.unknowntld"), "unknowntld")
        self.assertEqual(self.psl.publicsuffix("unknowntld"), "unknowntld")

        self.assertEqual(self.psl.publicsuffix("www.example.unknowntld", accept_unknown=True), "unknowntld")
        self.assertEqual(self.psl.publicsuffix("unknowntld", accept_unknown=True), "unknowntld")
        self.assertEqual(self.psl.publicsuffix("www.example.unknowntld", accept_unknown=False), None)
        self.assertEqual(self.psl.publicsuffix("unknowntld", accept_unknown=False), None)

    def test_deny_unknown(self):
        source = """
known
"""
        psl = PublicSuffixList(source.splitlines(), accept_unknown=False)

        self.assertEqual(psl.suffix("www.example.unknowntld"), None)

    def test_custom_psl(self):
        source = """
invalid
*.invalid
!test.invalid
"""
        psl = PublicSuffixList(source.splitlines())

        self.assertEqual(psl.suffix("example.invalid"), None)
        self.assertEqual(psl.suffix("test.invalid"), "test.invalid")
        self.assertEqual(psl.suffix("some.test.invalid"), "test.invalid")
        self.assertEqual(psl.suffix("aaa.bbb.ccc.invalid"), "bbb.ccc.invalid")

        self.assertEqual(psl.publicsuffix("example.invalid"), "example.invalid")
        self.assertEqual(psl.publicsuffix("test.invalid"), "invalid")

    def test_publicsuffix(self):
        self.assertEqual(self.psl.publicsuffix("www.example.com"), "com")
        self.assertEqual(self.psl.publicsuffix("unknowntld"), "unknowntld")

    def test_wildcard(self):
        self.assertEqual(self.psl.suffix("test.example.nagoya.jp"), "test.example.nagoya.jp")
        self.assertEqual(self.psl.suffix("example.nagoya.jp"), None)
        self.assertEqual(self.psl.publicsuffix("example.nagoya.jp"), "example.nagoya.jp")
        self.assertEqual(self.psl.publicsuffix("test.example.nagoya.jp"), "example.nagoya.jp")

    def test_checkpublicsuffix_script(self):
        regex = re.compile(r"^checkPublicSuffix\(('[^']+'), (null|'[^']+')\);")
        with open(os.path.join(os.path.dirname(__file__), "test_psl.txt"), "rb") as f:
            ln = 0

            for line in f:
                ln += 1
                l = line.decode("utf-8")
                m = regex.match(l)
                if not m:
                    continue

                arg = m.group(1).strip("'")
                res = None if m.group(2) == "null" else m.group(2).strip("'")

                self.assertEqual(self.psl.suffix(arg), res, "in line {0}: {1}".format(ln, line.strip()))

    def test_typeerror(self):

        self.assertRaises(TypeError, lambda: self.psl.suffix(None))
        self.assertRaises(TypeError, lambda: self.psl.suffix(1))
        if b("") != "":
            # python3
            self.assertRaises(TypeError, lambda: self.psl.suffix(b("www.example.com")))

    def test_bytestuple(self):
        psl = self.psl
        data = (b"www", b"example", b"com")
        pubres  = (b"com",)
        privres = (b"example", b"com")
        self.assertEqual(psl.publicsuffix(data), pubres)
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_bytestuple_punycode(self):
        source = """
example
例.example
"""
        psl = PublicSuffixList(source)
        # punycoded ASCII should match
        data = bytestuple("aaa.www.例.example".encode("idna"))
        pubres  = data[-2:] # xn--fsq.example
        privres = data[-3:]
        self.assertEqual(psl.publicsuffix(data), pubres)
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_bytestuple_utf8(self):
        source = """
example
例.example
"""
        psl = PublicSuffixList(source)
        # UTF-8 encoded bytes should NOT match
        data = bytestuple("aaa.www.例.example".encode("utf8"))
        pubres  = data[-1:] # example
        privres = data[-2:]
        self.assertEqual(psl.publicsuffix(data), pubres)
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_bytestuple_otherencoding(self):
        source = """
example
例.example
"""
        psl = PublicSuffixList(source.splitlines())
        # Shift_JIS encoded bytes should NOT match
        data = bytestuple("aaa.www.例.example".encode("sjis"))
        pubres  = data[-1:] # example
        privres = data[-2:]
        self.assertEqual(psl.publicsuffix(data), pubres)
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_bytestuple_empty(self):
        psl = self.psl
        self.assertEqual(psl.publicsuffix(()), None)
        self.assertEqual(psl.privatesuffix(()), None)

    def test_bytestuple_noneresult(self):
        psl = self.psl
        data = (b"com",)
        pubres  = (b"com",)
        privres = None

        self.assertEqual(psl.publicsuffix(data), pubres)
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_wrongtuple_resulttype(self):
        psl = self.psl
        data = tuple("www.example.com".split("."))
        self.assertRaises(TypeError, lambda: psl.suffix(data))

    def test_byteslist_resulttype(self):
        psl = self.psl
        data = bytestuple(b"www.example.com")
        privres = bytestuple(b"example.com")

        data_list = list(data)
        self.assertEqual(psl.privatesuffix(data_list), privres)

    def test_bytesgen_resulttype(self):
        psl = self.psl
        data = bytestuple(b"www.example.com")
        privres = bytestuple(b"example.com")
        data_gen = (x for x in data)

        self.assertEqual(psl.privatesuffix(data_gen), privres)

    def test_bytestuple_lowercase(self):
        psl = self.psl
        data = tuple(b"TesT.WwW.ExamplE.CoM".split(b"."))
        privres = tuple(b"example.com".split(b"."))
        self.assertEqual(psl.privatesuffix(data), privres)

    def test_bytestuple_keepcase(self):
        psl = self.psl
        data = tuple(b"TesT.WwW.ExamplE.CoM".split(b"."))
        privres = tuple(b"ExamplE.CoM".split(b"."))
        self.assertEqual(psl.privatesuffix(data, keep_case=True), privres)

    def test_compatclass(self):

        from publicsuffixlist.compat import PublicSuffixList
        psl = PublicSuffixList()

        self.assertEqual(psl.get_public_suffix("test.example.com"), "example.com")
        self.assertEqual(psl.get_public_suffix("com"), "")
        self.assertEqual(psl.get_public_suffix(""), "")

    def test_unsafecompatclass(self):

        from publicsuffixlist.compat import UnsafePublicSuffixList
        psl = UnsafePublicSuffixList()

        self.assertEqual(psl.get_public_suffix("test.example.com"), "example.com")
        self.assertEqual(psl.get_public_suffix("com"), "com")
        self.assertEqual(psl.get_public_suffix(""), "")

    def test_toomanylabels(self):
        d = "a." * 1000000 + "example.com"

        self.assertEqual(self.psl.publicsuffix(d), "com")
        self.assertEqual(self.psl.privatesuffix(d), "example.com")

    def test_flatstring(self):
        psl = PublicSuffixList(u("com\nnet\n"))
        self.assertEqual(psl.publicsuffix("example.com"), "com")

    def test_flatbytestring(self):
        psl = PublicSuffixList(b("com\nnet\n"))
        self.assertEqual(psl.publicsuffix("example.com"), "com")

    def test_privateparts(self):
        psl = self.psl
        self.assertEqual(psl.privateparts("Jp"), None)
        self.assertEqual(psl.privateparts("Co.Jp"), None)
        self.assertEqual(psl.privateparts("Example.Co.Jp"), ("example.co.jp",))
        self.assertEqual(psl.privateparts("Www.Example.Co.Jp"), ("www", "example.co.jp"))
        self.assertEqual(psl.privateparts("Aaa.Www.Example.Co.Jp"), ("aaa", "www", "example.co.jp"))

    def test_privateparts_keepcase(self):
        psl = self.psl
        self.assertEqual(psl.privateparts("Aaa.Www.Example.Co.Jp", keep_case=True),
                                   ("Aaa", "Www", "Example.Co.Jp"))

    def test_noprivateparts(self):
        psl = self.psl
        self.assertEqual(psl.privateparts("com"), None)  # no private part

    def test_reconstructparts(self):
        psl = self.psl
        self.assertEqual(".".join(psl.privateparts("aaa.www.example.com")), "aaa.www.example.com")

    def test_subdomain(self):
        psl = self.psl
        self.assertEqual(psl.subdomain("Aaa.Www.Example.Co.Jp", depth=0), "example.co.jp")
        self.assertEqual(psl.subdomain("Aaa.Www.Example.Co.Jp", depth=1), "www.example.co.jp")
        self.assertEqual(psl.subdomain("Aaa.Www.Example.Co.Jp", depth=2), "aaa.www.example.co.jp")
        self.assertEqual(psl.subdomain("Aaa.Www.Example.Co.Jp", depth=3), None)  # no sufficient depth

        # not private suffix
        self.assertEqual(psl.subdomain("Com", depth=0), None)
        self.assertEqual(psl.subdomain("Com", depth=1), None)

    def test_subdomain_keep_case(self):
        psl = self.psl
        self.assertEqual(psl.subdomain("Aaa.Www.Example.Co.Jp", depth=1, keep_case=True),
                                           "Www.Example.Co.Jp")
        self.assertEqual(psl.subdomain(bytestuple(b"Aaa.Www.Example.Co.Jp"), depth=1, keep_case=True),
                                           bytestuple(b"Www.Example.Co.Jp"))


    def test_wildcardonlytld(self):
        source = """
*.bd
"""
        psl = PublicSuffixList(source.splitlines(), accept_unknown=False)

        self.assertEqual(psl.publicsuffix("bd"), "bd")
        self.assertEqual(psl.privatesuffix("bd"), None)

        self.assertEqual(psl.publicsuffix("example.bd"), "example.bd")
        self.assertEqual(psl.privatesuffix("example.bd"), None)

        self.assertEqual(psl.publicsuffix("example.example.bd"), "example.bd")
        self.assertEqual(psl.privatesuffix("example.example.bd"), "example.example.bd")


    def test_longwildcard(self):
        source = """
com
*.compute.example.com
"""
        psl = PublicSuffixList(source.splitlines())

        self.assertEqual(psl.publicsuffix("com"), "com")
        self.assertEqual(psl.privatesuffix("com"), None)

        self.assertEqual(psl.publicsuffix("example.com"), "com")
        self.assertEqual(psl.privatesuffix("example.com"), "example.com")

        # wildcard implies the root is also public suffix
        self.assertEqual(psl.publicsuffix("compute.example.com"), "compute.example.com")
        self.assertEqual(psl.privatesuffix("compute.example.com"), None)

        self.assertEqual(psl.publicsuffix("region.compute.example.com"), "region.compute.example.com")
        self.assertEqual(psl.privatesuffix("region.compute.example.com"), None)

        self.assertEqual(psl.publicsuffix("user.region.compute.example.com"), "region.compute.example.com")
        self.assertEqual(psl.privatesuffix("user.region.compute.example.com"), "user.region.compute.example.com")

        self.assertEqual(psl.publicsuffix("sub.user.region.compute.example.com"), "region.compute.example.com")
        self.assertEqual(psl.privatesuffix("sub.user.region.compute.example.com"), "user.region.compute.example.com")

        # mismatch in the middle
        self.assertEqual(psl.publicsuffix("user.region.not-compute.example.com"), "com")
        self.assertEqual(psl.privatesuffix("user.region.not-compute.example.com"), "example.com")

    def test_is_utilities_mixcase(self):
        psl = self.psl
        self.assertEqual(psl.is_private("Jp"), False)
        self.assertEqual(psl.is_private("Co.Jp"), False)
        self.assertEqual(psl.is_private("Example.Co.Jp"), True)
        self.assertEqual(psl.is_private("Www.Example.Co.Jp"), True)
        self.assertEqual(psl.is_public("Jp"), True)
        self.assertEqual(psl.is_public("Co.Jp"), True)
        self.assertEqual(psl.is_public("Example.Co.Jp"), False)
        self.assertEqual(psl.is_public("Www.Example.Co.Jp"), False)


class TestPSLSections(unittest.TestCase):

    def test_icann(self):
        psl = PublicSuffixList(only_icann=True)
        self.assertEqual(psl.publicsuffix("www.example.com"), 'com')
        self.assertEqual(psl.publicsuffix("example.priv.at"), 'at')

    def test_icann_section_detection_custom_source(self):
        # Only rules inside the ICANN section should be honoured when
        # only_icann=True.  The "private" rule must be ignored.
        source = (
            "// ===BEGIN ICANN DOMAINS===\n"
            "icann\n"
            "// ===END ICANN DOMAINS===\n"
            "private\n"
        )
        psl = PublicSuffixList(source, only_icann=True)
        # "icann" rule was in the ICANN section → treated as explicit public suffix
        self.assertIsNone(psl.privatesuffix("icann"))
        self.assertEqual(psl.publicsuffix("icann"), "icann")
        self.assertEqual(psl.publicsuffix("example.icann"), "icann")
        self.assertEqual(psl.privatesuffix("example.icann"), "example.icann")
        # "private" rule was outside the ICANN section → falls through to the
        # unknown-TLD path (accept_unknown=True default), so it still acts as
        # a public suffix but only by the unknown-TLD rule, not an explicit one.
        self.assertEqual(psl.publicsuffix("example.private"), "private")
        self.assertEqual(psl.privatesuffix("example.private"), "example.private")

    def test_icann_no_markers(self):
        # When the source has no ICANN section markers, only_icann=True means
        # section_is_icann stays None (falsy) for every line → nothing is
        # added to the suffix set, so all lookups fall back to accept_unknown.
        source = "com\nnet\n"
        psl = PublicSuffixList(source, only_icann=True)
        # With accept_unknown=True (default) an unknown single-label TLD is
        # still treated as public, so "example.com" gets a private suffix via
        # the unknown-TLD path.
        self.assertEqual(psl.privatesuffix("example.com"), "example.com")
        # An explicit ICANN entry was never loaded, so "com" itself is treated
        # as an unknown TLD (public) rather than as an explicitly listed suffix.
        self.assertIsNone(psl.privatesuffix("com"))

    def test_icann_private_domain_excluded(self):
        # github.io is a private-section entry in the real PSL.
        # With only_icann=True it should not be honoured as a public suffix,
        # so "pages.github.io" should have a private suffix (via unknown-TLD
        # fallback) rather than returning None.
        psl = PublicSuffixList(only_icann=True)
        result = psl.privatesuffix("pages.github.io")
        self.assertIsNotNone(result)


class TestHelpers(unittest.TestCase):

    def test_u_function(self):
        # bytes → str
        self.assertEqual(u(b"hello"), "hello")
        self.assertIsInstance(u(b"hello"), str)
        # str passthrough
        self.assertEqual(u("hello"), "hello")
        self.assertIsInstance(u("hello"), str)

    def test_b_function(self):
        # str → bytes
        self.assertEqual(b("hello"), b"hello")
        self.assertIsInstance(b("hello"), bytes)
        # bytes passthrough
        self.assertEqual(b(b"hello"), b"hello")
        self.assertIsInstance(b(b"hello"), bytes)
        # bytearray → bytes
        self.assertEqual(b(bytearray(b"hello")), b"hello")
        self.assertIsInstance(b(bytearray(b"hello")), bytes)

    def test_encode_idn(self):
        result = encode_idn(u("例.jp"))
        # Must be pure ASCII (punycode)
        result.encode("ascii")
        self.assertIn("jp", result)
        self.assertNotIn("例", result)

    def test_decode_idn(self):
        original = u("例.jp")
        encoded = encode_idn(original)
        self.assertEqual(decode_idn(encoded), original)

    def test_decode_idn_invalid(self):
        # Invalid punycode must raise UnicodeError rather than silently produce
        # a meaningless result.
        self.assertRaises(UnicodeError, lambda: decode_idn("xn--invalid-punycode-zzzzzz.jp"))


class TestConstructorOptions(unittest.TestCase):

    def test_accept_encoded_idn_false(self):
        # With accept_encoded_idn=False the punycode variant of an IDN rule is
        # NOT added to the suffix set, so a punycoded domain that matches the
        # IDN rule should fall back to the unknown-TLD path instead of being
        # treated as a known public suffix in the usual way.
        source = u("例.jp\n")
        psl_with = PublicSuffixList(source, accept_encoded_idn=True)
        psl_without = PublicSuffixList(source, accept_encoded_idn=False)

        puny_tld = encode_idn(u("例.jp"))  # e.g. "xn--fsq.jp"
        domain = "test." + puny_tld       # e.g. "test.xn--fsq.jp"

        # With encoding enabled the punycoded rule is loaded → private suffix
        # has exactly one private label.
        self.assertEqual(psl_with.privatesuffix(domain), domain)

        # Without encoding the punycoded rule is absent → only the base "jp"
        # rule (via unknown TLD fallback or explicit jp) applies, so the
        # private suffix includes more of the domain.
        result_without = psl_without.privatesuffix(domain)
        self.assertNotEqual(result_without, domain)


class TestIsPrivatePublicEdgeCases(unittest.TestCase):

    def setUp(self):
        self.psl = PublicSuffixList()

    def test_is_private_invalid_domain(self):
        self.assertFalse(self.psl.is_private(".bad"))
        self.assertFalse(self.psl.is_private(""))
        self.assertFalse(self.psl.is_private("www..invalid"))

    def test_is_public_invalid_domain(self):
        self.assertFalse(self.psl.is_public(".bad"))
        self.assertFalse(self.psl.is_public(""))
        self.assertFalse(self.psl.is_public("www..invalid"))

    def test_is_private_unknown_tld(self):
        # Two-label domain under unknown TLD → private (registrable)
        self.assertTrue(self.psl.is_private("example.unknowntld"))
        # Three-label domain under unknown TLD → still private
        self.assertTrue(self.psl.is_private("sub.example.unknowntld"))

    def test_is_public_unknown_tld(self):
        # Single unknown TLD → public
        self.assertTrue(self.psl.is_public("unknowntld"))
        # Two-label domain under unknown TLD → not public
        self.assertFalse(self.psl.is_public("example.unknowntld"))

    def test_is_private_is_public_trailing_dot(self):
        # Trailing dot is ignored; domain reduces to valid form
        self.assertTrue(self.psl.is_private("example.com."))
        self.assertFalse(self.psl.is_public("example.com."))

    def test_is_public_known_tld(self):
        self.assertTrue(self.psl.is_public("com"))
        self.assertTrue(self.psl.is_public("co.jp"))
        self.assertFalse(self.psl.is_public("example.com"))


class TestPrivatepartsBytestuple(unittest.TestCase):

    def setUp(self):
        self.psl = PublicSuffixList()

    def test_privateparts_bytestuple_basic(self):
        data = (b"www", b"example", b"com")
        result = self.psl.privateparts(data)
        # subdomain labels + private suffix tuple
        self.assertEqual(result, (b"www", (b"example", b"com")))

    def test_privateparts_bytestuple_no_subdomain(self):
        data = (b"example", b"com")
        result = self.psl.privateparts(data)
        self.assertEqual(result, ((b"example", b"com"),))

    def test_privateparts_bytestuple_keepcase(self):
        data = (b"Www", b"Example", b"Com")
        result = self.psl.privateparts(data, keep_case=True)
        self.assertEqual(result, (b"Www", (b"Example", b"Com")))

    def test_privateparts_bytestuple_none(self):
        # public suffix only → no private part
        data = (b"com",)
        self.assertIsNone(self.psl.privateparts(data))


class TestSubdomainBytestuple(unittest.TestCase):

    def setUp(self):
        self.psl = PublicSuffixList()

    def test_subdomain_bytestuple_depth0(self):
        data = (b"aaa", b"www", b"example", b"com")
        result = self.psl.subdomain(data, depth=0)
        self.assertEqual(result, (b"example", b"com"))

    def test_subdomain_bytestuple_depth1(self):
        data = (b"aaa", b"www", b"example", b"com")
        result = self.psl.subdomain(data, depth=1)
        self.assertEqual(result, (b"www", b"example", b"com"))

    def test_subdomain_bytestuple_overflow(self):
        data = (b"example", b"com")
        # depth=1 requires at least 3 labels (publen=1 + 1 private + 1 sub)
        self.assertIsNone(self.psl.subdomain(data, depth=1))

    def test_subdomain_bytestuple_public_only(self):
        data = (b"com",)
        self.assertIsNone(self.psl.subdomain(data, depth=0))


class TestBytearrayTypeError(unittest.TestCase):

    def setUp(self):
        self.psl = PublicSuffixList()

    def test_bytearray_raises_typeerror(self):
        self.assertRaises(TypeError, lambda: self.psl.suffix(bytearray(b"example.com")))

    def test_bytearray_publicsuffix_raises_typeerror(self):
        self.assertRaises(TypeError, lambda: self.psl.publicsuffix(bytearray(b"example.com")))

    def test_bytearray_privatesuffix_raises_typeerror(self):
        self.assertRaises(TypeError, lambda: self.psl.privatesuffix(bytearray(b"example.com")))


class TestWildcardAcceptUnknown(unittest.TestCase):

    def setUp(self):
        source = "*.bd\n"
        # accept_unknown=True is the default; test it explicitly as well
        self.psl = PublicSuffixList(source.splitlines(), accept_unknown=True)

    def test_bare_tld_is_public(self):
        self.assertEqual(self.psl.publicsuffix("bd"), "bd")
        self.assertIsNone(self.psl.privatesuffix("bd"))

    def test_one_label_under_wildcard_is_public(self):
        # "example.bd" matches *.bd → example.bd is public suffix
        self.assertEqual(self.psl.publicsuffix("example.bd"), "example.bd")
        self.assertIsNone(self.psl.privatesuffix("example.bd"))

    def test_two_labels_under_wildcard_has_private(self):
        self.assertEqual(self.psl.publicsuffix("sub.example.bd"), "example.bd")
        self.assertEqual(self.psl.privatesuffix("sub.example.bd"), "sub.example.bd")


class TestCompatEdgeCases(unittest.TestCase):

    def setUp(self):
        from publicsuffixlist.compat import PublicSuffixList, UnsafePublicSuffixList
        self.psl = PublicSuffixList()
        self.upsl = UnsafePublicSuffixList()

    def test_compat_unknown_tld(self):
        self.assertEqual(self.psl.get_public_suffix("example.unknowntld"), "example.unknowntld")

    def test_compat_invalid_domain(self):
        self.assertEqual(self.psl.get_public_suffix(".bad"), "")

    def test_compat_empty_string(self):
        self.assertEqual(self.psl.get_public_suffix(""), "")

    def test_compat_very_long_domain(self):
        d = "a." * 1000 + "example.com"
        self.assertEqual(self.psl.get_public_suffix(d), "example.com")

    def test_unsafe_compat_fallback_public_suffix(self):
        # When privatesuffix is None (e.g. bare TLD), UnsafePublicSuffixList
        # falls back to returning the publicsuffix instead.
        self.assertEqual(self.upsl.get_public_suffix("com"), "com")

    def test_unsafe_compat_private_domain(self):
        self.assertEqual(self.upsl.get_public_suffix("test.example.com"), "example.com")

    def test_unsafe_compat_invalid_domain(self):
        self.assertEqual(self.upsl.get_public_suffix(".bad"), "")

    def test_unsafe_compat_empty_string(self):
        self.assertEqual(self.upsl.get_public_suffix(""), "")


class TestLargePSLSource(unittest.TestCase):

    def test_many_rules_parsing(self):
        # Build a PSL with thousands of rules and verify lookups stay correct.
        lines = ["// ===BEGIN ICANN DOMAINS==="]
        lines += ["rule{0}.example".format(i) for i in range(500)]
        lines += ["// ===END ICANN DOMAINS==="]
        lines += ["com"]
        source = "\n".join(lines)
        psl = PublicSuffixList(source)
        # An explicitly listed suffix should be recognised
        self.assertIsNone(psl.privatesuffix("rule42.example"))
        self.assertEqual(psl.publicsuffix("rule42.example"), "rule42.example")
        # A sub-domain of that rule should be private
        self.assertEqual(psl.privatesuffix("sub.rule42.example"), "sub.rule42.example")
        # Standard TLD still works
        self.assertEqual(psl.privatesuffix("example.com"), "example.com")


if __name__ == "__main__":
    unittest.main()
