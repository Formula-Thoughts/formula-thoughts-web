from setuptools import setup, find_packages

DESCRIPTION = 'A web library for AWS lambda, gateway and SQS event handling'
LONG_DESCRIPTION = 'Allows for handling http api gateway requests, and SQS events'
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

# Setting up
setup(
    name="python-autofixture",
    version="{{VERSION_PLACEHOLDER}}",
    author="GanTheMan",
    author_email="aidanwilliamgannon@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    keywords=['python', 'lambda', 'api gateway', 'sqs'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix"
    ]
)