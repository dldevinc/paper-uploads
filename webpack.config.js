import path from "path";
import webpack from "webpack";
import { fileURLToPath } from "url";
import { merge } from "webpack-merge";
import TerserPlugin from "terser-webpack-plugin";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import CssMinimizerPlugin from "css-minimizer-webpack-plugin";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SOURCE_DIR = path.resolve(__dirname, "paper_uploads/static/paper_uploads/src");
const DIST_DIR = path.resolve(__dirname, "paper_uploads/static/paper_uploads/dist");

// Базовый объект, чьи свойства наследуют все конфигурации.
function getCommonConfig(devMode) {
    return {
        mode: devMode ? "development" : "production",
        devtool: devMode ? "eval" : "source-map",
        cache: devMode
            ? {
                type: "filesystem",
                cacheDirectory: path.resolve(__dirname, "cache"),
                buildDependencies: {
                    config: [__filename]
                }
            }
            : false,
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    exclude: /[\\/]node_modules[\\/]/,
                    loader: "babel-loader",
                    options: devMode
                        ? {
                            cacheDirectory: path.resolve(__dirname, "cache")
                        }
                        : {}
                },

                {
                    test: /\.css$/,
                    use: [
                        {
                            loader: MiniCssExtractPlugin.loader
                        },
                        {
                            loader: "fast-css-loader",
                            options: {
                                importLoaders: 1
                            }
                        },
                        {
                            loader: "postcss-loader"
                        }
                    ]
                },

                {
                    test: /\.scss$/,
                    use: [
                        {
                            loader: MiniCssExtractPlugin.loader
                        },
                        {
                            loader: "fast-css-loader",
                            options: {
                                importLoaders: 2
                            }
                        },
                        {
                            loader: "postcss-loader"
                        },
                        {
                            loader: "sass-loader",
                            options: {
                                sassOptions: {
                                    includePaths: [
                                        path.resolve(SOURCE_DIR, "css"),
                                        path.resolve(__dirname, "node_modules")
                                    ]
                                }
                            }
                        }
                    ]
                },

                {
                    test: /\.(jpe?g|png|gif|woff2?|ttf|eot|svg)$/i,
                    type: "asset/resource"
                },

                // https://webpack.js.org/guides/asset-modules/#replacing-inline-loader-syntax
                {
                    resourceQuery: /raw/,
                    type: "asset/source"
                }
            ]
        },
        resolve: {
            modules: [SOURCE_DIR, "node_modules"]
        },
        plugins: [
            new webpack.ProgressPlugin(),
            new MiniCssExtractPlugin({
                filename: "[name].css"
            })
        ],
        optimization: {
            moduleIds: "deterministic",
            minimizer: [].concat(
                devMode
                    ? []
                    : [
                        new TerserPlugin({
                            parallel: true
                        }),
                        new CssMinimizerPlugin({})
                    ]
            )
        },
        watchOptions: {
            aggregateTimeout: 2000,
            ignored: ["**/node_modules"]
        },
        stats: {
            assets: false,
            chunks: true
        }
    };
}

// Конфигурация общих ресурсов, которые будут загружены в defer-режиме.
function getAppConfig(devMode) {
    return merge(getCommonConfig(devMode), {
        entry: {
            widget: path.resolve(SOURCE_DIR, "js/widget.js")
        },
        output: {
            clean: true,
            path: path.resolve(DIST_DIR),
            publicPath: "/static/paper_uploads/dist/",
            filename: "[name].js",
            assetModuleFilename: "assets/[name][ext][query]",
            library: {
                type: "window"
            }
        }
    });
}

export default (env, argv) => {
    const devMode = argv.mode !== "production";
    return [getAppConfig(devMode)];
};
