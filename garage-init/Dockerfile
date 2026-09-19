# The Garage image ships a single static binary and no shell, so the CLI is
# lifted into an image that has one and can run the provisioning script.
FROM dxflrs/garage:v2.4.1 AS garage

FROM alpine:3.22

COPY --from=garage /garage /usr/local/bin/garage
COPY init.sh /init.sh

ENTRYPOINT ["/bin/sh", "/init.sh"]
