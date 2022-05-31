import setuptools

setuptools.setup(
    name="anopcb-server",
    version="2.0",
    scripts=["anopcb-server"],
    author="IMMS",
    author_email="julian.kuners@imms.de",
    description="The machine-learning server for the anopcb kicad plugin.",
    # url="https://github.com/javatechy/dokr",
    packages=["Server"],
    include_package_data=True,
    package_data={"Server": ["datasets/", "datasets/*", "models/", "models/*"]},
    install_requires=["tensorflow", "numpy", "numba"],
    classifiers=[],
)
