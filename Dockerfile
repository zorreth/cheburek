FROM oven/bun:1 AS base
WORKDIR /app

FROM base AS install
RUN mkdir -p /temp/dev
COPY package.json bun.lock /temp/dev/
RUN cd /temp/dev && bun install --frozen-lockfile

FROM base AS release
COPY --from=install /temp/dev/node_modules node_modules
COPY . .

RUN mkdir -p /app/data && chown -R bun:bun /app/data

USER bun
ENTRYPOINT ["bun", "run", "index.ts"]
