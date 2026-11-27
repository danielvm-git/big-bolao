from bolao import links


def test_signed_link_verifies():
    assert links.verify(123, links.sign(123, "s3cret"), "s3cret")


def test_changed_uid_fails():
    assert not links.verify(124, links.sign(123, "s3cret"), "s3cret")


def test_no_secret_or_no_sig_fails():
    assert not links.verify(123, links.sign(123, "s3cret"), "")
    assert not links.verify(123, None, "s3cret")
    assert not links.verify("abc", "x", "s3cret")
